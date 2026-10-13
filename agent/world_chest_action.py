import ctypes
from ctypes import wintypes

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction


def chest_center(box):
    x, y, w, h = box
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x+w > 1920 or y+h > 1080:
        raise ValueError('Invalid 1080p chest detection box')
    return x+w//2, y+h//2


def game_is_foreground():
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(user32.GetForegroundWindow(), title, len(title))
    return title.value == 'Last Epoch'


@AgentServer.custom_action('ClickWorldChestOnce')
class ClickWorldChestOnce(CustomAction):
    def run(self, context, argv):
        try:
            if context.tasker.stopping or not game_is_foreground():
                raise RuntimeError('Keep Last Epoch foreground for this click test')
            if argv.reco_detail is None or not argv.reco_detail.hit:
                raise ValueError('Chest recognition was not confirmed')
            x,y = chest_center(argv.box)
            print(f'Chest click test: one click at 1080p coordinates ({x}, {y})', flush=True)
            return context.tasker.controller.post_click(x,y).wait().succeeded
        except Exception as exc:
            print(f'Chest click test failed: {exc}', flush=True)
            return False
