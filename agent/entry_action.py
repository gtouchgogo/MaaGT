from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from interaction_actions import InteractionIO
from world_chest_action import chest_center
from vision_worker_client import request_vision


def enter_inside(io,observe,max_charges=30):
    charges=0
    for _ in range(max_charges+8):
        report=observe()
        controls=report['entry_controls']
        if report['zone']=='inside':
            raise RuntimeError('Entry task must start at Outside selector, not inside a run')
        if controls['confirm']['box']:
            io.click(chest_center(controls['confirm']['box']))
            io.wait(.5)
            break
        if controls['boss_ready']['box']:
            io.click(chest_center(controls['boss_ready']['box']),button=1)
            io.wait(.5)
            break
        if controls['charge']['box'] and charges<max_charges:
            io.click(chest_center(controls['charge']['box']))
            charges+=1
            io.wait(.25)
            continue
        raise RuntimeError('Selector controls uncertain or charge limit reached')
    else:
        raise RuntimeError('Entry attempt limit reached')
    consecutive=0
    for _ in range(40):
        zone=io.observe()['zone']
        consecutive=consecutive+1 if zone=='inside' else 0
        if consecutive>=2:
            io.wait(.3)
            return
        io.wait(.25)
    raise RuntimeError('Entry sent but loaded Inside zone was not confirmed')


@AgentServer.custom_action('EnterInsideFromSelector')
class EnterInsideFromSelector(CustomAction):
    def run(self,context,argv):
        try:
            io=InteractionIO(context)
            def observe():
                report=request_vision(io.snapshot(),'entry_detect_worker.py',timeout=10)
                io.guard()
                if report['inventory_full']:
                    raise RuntimeError('Inventory full; entry task stopped')
                print('Entry controls:',report['entry_controls'],flush=True)
                return report
            enter_inside(io,observe)
            print('Inside confirmed; starting the recorded route.',flush=True)
            return True
        except Exception as exc:
            print(f'Inside entry failed: {exc}',flush=True)
            return False


@AgentServer.custom_action('AbortUncertainInside')
class AbortUncertainInside(CustomAction):
    def run(self,context,argv):
        print('Inside target uncertain; full round stopped for inspection. No portal opened.',flush=True)
        return False
