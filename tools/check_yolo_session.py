"""Offline two-request smoke test; no controller or game inputs."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'agent'))
from yolo_session import detect_yolo, close_yolo


def main():
    image = cv2.imdecode(np.fromfile(ROOT / 'debug/world-yolo/offline-sample-raw.png',
                                   dtype=np.uint8), cv2.IMREAD_COLOR)
    try:
        first = detect_yolo(image)
        second = detect_yolo(image)
        assert first['target'] and first['target'] == second['target']
        assert first['worker_pid'] == second['worker_pid']
        assert first['model_loads'] == second['model_loads'] == 1
        print(json.dumps({'pid': first['worker_pid'], 'model_loads': 1,
                          'target': second['target'],
                          'request_ms': [first['request_ms'], second['request_ms']]}))
    finally:
        close_yolo()


if __name__ == '__main__':
    main()
