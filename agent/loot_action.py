import json
import subprocess
import time
from pathlib import Path
import numpy as np

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from world_chest_action import game_is_foreground

ROOT = Path(__file__).resolve().parent.parent


def pick_loop(snapshot, detect, click, wait, guard, max_checks=60):
    empty, unchanged, previous, clicks = 0,0,None,0
    for _ in range(max_checks):
        guard()
        result = detect(snapshot())
        guard()
        if result['inventory_full']:
            raise RuntimeError('Inventory full; loot task stopped')
        items = result['items']
        if not items:
            empty += 1
            if empty >= 2:
                return clicks
            wait(.35)
            continue
        empty = 0
        signature = tuple((i['kind'],tuple(i['box'])) for i in items)
        unchanged = unchanged+1 if signature == previous else 0
        if unchanged >= 5:
            raise RuntimeError('Loot made no progress; task stopped for inspection')
        previous = signature
        x,y,w,h = items[0]['box']
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x+w > 1920 or y+h > 1080:
            raise ValueError('Invalid loot detection box')
        guard()
        click(x+w//2,y+h//2)
        clicks += 1
        wait(.8)
    raise RuntimeError('Loot check limit reached; inspect remaining labels')


@AgentServer.custom_action('PickPinkOrangeLoot')
class PickPinkOrangeLoot(CustomAction):
    def run(self,context,argv):
        try:
            runtime = json.loads((ROOT/'tools'/'yolo_runtime.json').read_text(encoding='utf-8'))
            folder = ROOT/'debug'/'loot'
            folder.mkdir(parents=True,exist_ok=True)
            controller = context.tasker.controller

            def guard():
                if context.tasker.stopping or not game_is_foreground():
                    raise RuntimeError('Stopped or Last Epoch lost foreground focus')

            def wait(seconds):
                end = time.perf_counter()+seconds
                while time.perf_counter()<end:
                    guard()
                    time.sleep(min(.02,max(0,end-time.perf_counter())))

            def snapshot():
                guard()
                # Move without a button press to remove hovered loot styling.
                if not controller.post_touch_move(100,60,pressure=0).wait().succeeded:
                    raise RuntimeError('Cannot move cursor away from loot')
                wait(.12)
                if not controller.post_screencap().wait().succeeded:
                    raise RuntimeError('Loot capture failed')
                return controller.cached_image.copy()

            def detect(image):
                stem = str(time.time_ns())
                source,output = folder/f'{stem}.npy',folder/f'{stem}.json'
                np.save(source,image,allow_pickle=False)
                try:
                    job = subprocess.run([runtime['python'],str(ROOT/'tools'/'loot_detect_worker.py'),
                        '--input',str(source),'--output',str(output)],capture_output=True,text=True,
                        timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
                    if job.returncode:
                        raise RuntimeError(f'Loot detector failed: {job.stderr[-1500:]}')
                    report = json.loads(output.read_text(encoding='utf-8'))
                    print('Loot candidates:',json.dumps(report),flush=True)
                    return report
                finally:
                    source.unlink(missing_ok=True)

            def click(x,y):
                if not controller.post_click(x,y).wait().succeeded:
                    raise RuntimeError('Loot click failed')

            count = pick_loop(snapshot,detect,click,wait,guard)
            print(f'Loot finished after {count} clicks; two empty checks.',flush=True)
            return True
        except Exception as exc:
            print(f'Loot task failed: {exc}',flush=True)
            return False
