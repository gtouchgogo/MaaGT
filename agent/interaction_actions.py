import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from world_chest_action import game_is_foreground, chest_center
from vision_worker_client import request_vision, ROOT
from yolo_session import detect_yolo


class InteractionIO:
    def __init__(self,context):
        self.context=context
        self.controller=context.tasker.controller

    def guard(self):
        if self.context.tasker.stopping or not game_is_foreground():
            raise RuntimeError('Stopped or game lost foreground focus')

    def wait(self,seconds):
        end=time.perf_counter()+seconds
        while time.perf_counter()<end:
            self.guard()
            time.sleep(min(.02,max(0,end-time.perf_counter())))

    def snapshot(self):
        self.guard()
        if not self.controller.post_screencap().wait().succeeded:
            raise RuntimeError('Interaction capture failed')
        return self.controller.cached_image.copy()

    def key(self,key,duration):
        self.guard()
        try:
            if not self.controller.post_key_down(key).wait().succeeded:
                raise RuntimeError('Key down failed')
            self.wait(duration)
        finally:
            if not self.controller.post_key_up(key).wait().succeeded:
                raise RuntimeError('Key release failed')

    def click(self,point,button=0):
        self.guard()
        if not self.controller.post_click(*point,contact=button).wait().succeeded:
            raise RuntimeError('Interaction click failed')

    def observe(self):
        report=request_vision(self.snapshot(),'exit_detect_worker.py',timeout=10)
        self.guard()
        if report['inventory_full']:
            raise RuntimeError('Inventory full; task stopped')
        return report

    def target(self):
        report=self.observe()
        if report['text']:
            return chest_center(report['text'])
        if report['ring']:
            point=chest_center(report['ring'])
            self.guard()
            if not self.controller.post_touch_move(*point,pressure=0).wait().succeeded:
                raise RuntimeError('Cannot hover portal')
            self.wait(.15)
            hovered=self.observe()
            if hovered['text']:
                return chest_center(hovered['text'])
            return point
        return tuple(report['fixed_point'])


def exit_portal(io):
    status=io.observe()['zone']
    if status == 'outside':
        return
    if status != 'inside':
        raise RuntimeError('Cannot confirm inside before portal input')
    point=None
    for attempt,direction in enumerate((None,None,68,83,87)):
        if attempt == 0 or direction is not None:
            if direction:
                io.key(direction,.5)
                io.wait(.3)
            io.key(84,.08)
            io.wait(.8)
            point=io.target()
        io.click(point)
        io.wait(.5)
        outside,inside,unknown=0,0,0
        for _ in range(12):
            zone=io.observe()['zone']
            outside=outside+1 if zone == 'outside' else 0
            inside=inside+1 if zone == 'inside' else 0
            unknown=unknown+1 if zone is None else 0
            if outside >= 2:
                return
            if inside >= 3:
                break
            io.wait(.3)
        else:
            raise RuntimeError('Zone transition uncertain; stopping instead of moving during loading')
    raise RuntimeError('Exit failed after same-point retry and right/down/up attempts')


def activate_altar(io,detect):
    for direction in (None,83,65,68,87):
        if direction:
            io.key(direction,.5)
            io.wait(.3)
        report=detect(io.snapshot())
        io.guard()
        if report['target']:
            io.click(chest_center(report['target']))
            io.wait(2)
            return
    raise RuntimeError('Remembered altar not located after down/left/right/up recovery')


@AgentServer.custom_action('ActivateWorldAltar')
class ActivateWorldAltar(CustomAction):
    def run(self,context,argv):
        try:
            io=InteractionIO(context)
            def detect(image):
                return detect_yolo(image,'altar')
            activate_altar(io,detect)
            return True
        except Exception as exc:
            print(f'Altar activation failed: {exc}',flush=True)
            return False


@AgentServer.custom_action('ExitThroughPortal')
class ExitThroughPortal(CustomAction):
    def run(self,context,argv):
        try:
            exit_portal(InteractionIO(context))
            print('Outside confirmed; exit task finished.',flush=True)
            return True
        except Exception as exc:
            print(f'Portal exit failed: {exc}',flush=True)
            return False
