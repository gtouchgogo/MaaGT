"""Bounded round sessions, isolated by Maa task ID."""
import json
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from yolo_session import warm_yolo


class RoundSessions:
    def __init__(self):
        self.sessions = {}

    def begin(self, task_id, count, continuous=False):
        if not continuous and (type(count) is not int or not 1 <= count <= 100):
            raise ValueError('rounds must be an integer between 1 and 100')
        self.sessions.clear()
        self.sessions[task_id] = [None if continuous else count, 0]

    def finish(self, task_id):
        session = self.sessions.get(task_id)
        if session is None:
            return []
        session[1] += 1
        limit = session[0] if session[0] is not None else 'continuous'
        print(f'Completed rounds: {session[1]}/{limit}', flush=True)
        if session[0] is not None and session[1] >= session[0]:
            del self.sessions[task_id]
            return []
        return ['EnterInsideForRound']


sessions = RoundSessions()


@AgentServer.custom_action('BeginBoundedRounds')
class BeginBoundedRounds(CustomAction):
    continuous = False

    def run(self, context, argv):
        try:
            count = json.loads(argv.custom_action_param or '{}').get('rounds', 3)
            if context.tasker.stopping:
                return False
            # Warm before any movement, not during the timed route.
            warm_yolo()
            if context.tasker.stopping:
                return False
            sessions.begin(argv.task_detail.task_id, count, continuous=self.continuous)
            return True
        except Exception as exc:
            print(f'Cannot begin bounded rounds: {exc}', flush=True)
            return False


@AgentServer.custom_action('BeginContinuousRounds')
class BeginContinuousRounds(BeginBoundedRounds):
    continuous = True


@AgentServer.custom_action('FinishBoundedRound')
class FinishBoundedRound(CustomAction):
    def run(self, context, argv):
        if context.tasker.stopping:
            return False
        context.override_next(argv.node_name, sessions.finish(argv.task_detail.task_id))
        return True
