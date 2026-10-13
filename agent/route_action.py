"""按录制路线回放 WASD。打开小地图监控时，走路和识图同时进行，走完再改后续节点。"""
import json
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from route_clock import replay
from minimap_monitor import MinimapMonitor
from screenshot_process import ScreenshotProcess

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from convert_route import convert, WASD


@AgentServer.custom_action('ReplayRecordedRoute')
class ReplayRecordedRoute(CustomAction):
    """pipeline 里的 Custom 动作。run() 返回之前，MaaFW 不会执行本节点的 next。"""

    def run(self, context, argv):
        # 中途出错也要停监控、关截图进程，所以这两个对象放在 try 外面。
        monitor = None
        camera = None
        try:
            # custom_action_param 来自 pipeline，例如
            # {"route": "routes/inside.json", "monitor_minimap": true}
            params = json.loads(argv.custom_action_param or '{}')
            path = (ROOT / params.get('route', 'routes/inside.json')).resolve()
            if not path.is_relative_to((ROOT / 'routes').resolve()):
                raise ValueError('route must be inside the project routes directory')
            record = json.loads(path.read_text(encoding='utf-8-sig'))
            # convert 检查时间戳和按键是否成对。真正回放用的是下面抽出的按键边。
            _, report = convert(record)
            print('Route validation:', json.dumps(report), flush=True)
            # 只保留 W/A/S/D。鼠标移动和其他键不参与回放。
            # 每条边是 (相对起点的秒数, 虚拟键码, 按下还是松开)。
            edges = [(e['t'], e['vk'], e['down']) for e in record['events']
                     if e['kind'] == 'key' and e.get('vk') in WASD]
            # 发键走任务自己的控制器。截图如果也排进这个队列，回放时钟会被拖住。
            controller = context.tasker.controller
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]

            # 监控是可选项。没打开时，下面只回放按键。
            if params.get('monitor_minimap', False):
                hwnd = user32.GetForegroundWindow()
                title = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, title, len(title))
                if title.value != 'Last Epoch':
                    raise RuntimeError('Bring Last Epoch to foreground before monitored playback')
                # 单独一个进程截图并识别宝箱、祭坛。不占用 Agent 和按键共用的通信通道。
                camera = ScreenshotProcess(hwnd)

                def sample():
                    # 由监控线程周期调用，返回 {'chest': bool, 'altar': bool}。
                    return camera.detect()

                monitor = MinimapMonitor(sample)

            def stopping():
                # replay 在每个按键时间点之前调用。返回 True 会停掉路线并松开还按着的键。
                if monitor is not None and monitor.error:
                    raise RuntimeError(f'Minimap monitor failed: {monitor.error}')
                if context.tasker.stopping:
                    return True
                # 目前只在开跑前检查一次前景窗口。若要中途失焦就停，把下面四行恢复即可。
                # title = ctypes.create_unicode_buffer(512)
                # user32.GetWindowTextW(user32.GetForegroundWindow(), title, len(title))
                # if title.value != 'Last Epoch':
                #     raise RuntimeError('Last Epoch lost foreground focus; stopping route')
                return False

            def send(key, down):
                # post 只是把按键放进队列，必须 wait，否则记录时间会跑在实际按键前面。
                job = controller.post_key_down(key) if down else controller.post_key_up(key)
                return job.wait().succeeded

            # 先启动监控，再阻塞在回放里。两件事同时进行，直到路线结束。
            if monitor:
                monitor.start()
            ok = replay(edges, send, stopping)
            if monitor:
                # finish 会停掉监控线程，并给出看到了宝箱、祭坛，还是无法确定。
                result = monitor.finish()
                print('Minimap memory:', json.dumps(result), flush=True)
                # 路线完整走完才改 next。中途停止时 ok 为 False，沿用 pipeline 里原来的 next。
                if ok and not context.override_next(argv.node_name, [result['branch']]):
                    raise RuntimeError('Cannot select route result branch')
            return ok
        except Exception as exc:
            print(f'Route playback failed: {exc}', flush=True)
            return False
        finally:
            # 正常走完时上面已经 finish 过，这里只处理半路抛出的情况。
            if monitor and monitor.worker.is_alive():
                try:
                    monitor.finish()
                except Exception as exc:
                    print(f'Minimap cleanup failed: {exc}', flush=True)
            # 线程还在 detect() 里时不能关截图进程。
            if camera and (monitor is None or not monitor.worker.is_alive()):
                camera.close()
