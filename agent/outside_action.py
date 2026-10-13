import json

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from convert_route import convert,WASD
from route_clock import replay
from interaction_actions import InteractionIO
from world_chest_action import chest_center
from vision_worker_client import request_vision,ROOT

SELECTOR_BOX=(961,369,20,16)

def route_parts(record):
    convert(record)
    edges=[(e['t'],e['vk'],e['down']) for e in record['events']
           if e['kind']=='key' and e.get('vk') in WASD]
    screen=record.get('screen')
    if screen != [3840,2160]:
        raise ValueError('Outside recording must use the verified 3840x2160 layout')
    # Recorded mouse actions are intentionally ignored; use the calibrated 1080p point.
    return edges,chest_center(SELECTOR_BOX),0.


def open_selector(io,observe,first_point):
    # The caller confirmed Outside before movement; click immediately after key release.
    io.guard()
    io.click(first_point)
    io.wait(.35)
    for attempt in range(4):
        report=observe()
        if report['selector_open']:
            return
        if attempt==3:
            break
        if report['zone']!='outside' or not report['stone']:
            raise RuntimeError('Selector still closed; cannot safely locate stone core')
        io.click(chest_center(report['stone']))
        io.wait(.5)
    raise RuntimeError('Selector did not open after fixed click and three core retries')


@AgentServer.custom_action('ReturnOutsideToSelector')
class ReturnOutsideToSelector(CustomAction):
    def run(self,context,argv):
        try:
            io=InteractionIO(context)
            initial=request_vision(io.snapshot(),'stone_detect_worker.py',timeout=10)
            io.guard()
            if initial['inventory_full']:
                raise RuntimeError('Inventory full; task stopped')
            if initial['selector_open']:
                print('Map selector already open; no movement or click needed.',flush=True)
                return True
            if initial['zone']!='outside':
                raise RuntimeError('Outside route requires confirmed Outside zone')
            record=json.loads((ROOT/'routes/outside.json').read_text(encoding='utf-8-sig'))
            edges,point,pause=route_parts(record)
            print(f'Outside route: {len(edges)} key edges; movement {edges[-1][0]:.3f}s.',flush=True)

            def stopping():
                io.guard()
                return False

            def send(key,down):
                job=io.controller.post_key_down(key) if down else io.controller.post_key_up(key)
                return job.wait().succeeded

            if not replay(edges,send,stopping):
                return False
            io.wait(pause)

            def observe():
                result=request_vision(io.snapshot(),'stone_detect_worker.py',timeout=10)
                io.guard()
                if result['inventory_full']:
                    raise RuntimeError('Inventory full; task stopped')
                print('Selector state:',json.dumps(result),flush=True)
                return result

            open_selector(io,observe,point)
            print('Map selector open; single round complete. No next cycle started.',flush=True)
            return True
        except Exception as exc:
            print(f'Outside return failed: {exc}',flush=True)
            return False
