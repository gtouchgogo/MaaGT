import json
from pathlib import Path
from yolo_session import detect_yolo
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition

ROOT = Path(__file__).resolve().parent.parent


@AgentServer.custom_recognition('WorldChestYOLO')
class WorldChestYOLO(CustomRecognition):
    def analyze(self, context, argv):
        try:
            report=detect_yolo(argv.image,'chest')
            print('World YOLO:',json.dumps(report),flush=True)
            return CustomRecognition.AnalyzeResult(box=report['target'],detail=report)
        except Exception as exc:
            print(f'World YOLO failed: {exc}',flush=True)
            return CustomRecognition.AnalyzeResult(box=None,detail={'error':str(exc)})
