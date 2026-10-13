"""Persistent warmed inference worker. Reads frames, never controls the game."""
import argparse
import json
import os
import sys
import time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'agent'))
from monitor_protocol import publish_result
from world_yolo_detect import load_detector,detect_frame


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--model',type=Path,required=True)
    args=parser.parse_args()
    settings=ROOT/'debug'/'world-yolo'/'yolo-settings'
    settings.mkdir(parents=True,exist_ok=True)
    os.environ['YOLO_CONFIG_DIR']=str(settings)
    start=time.perf_counter()
    try:
        model,device=load_detector(args.model)
        publish_result(args.directory,'ready',True,hits={
            'pid':os.getpid(),'model_loads':1,'device':str(device),
            'startup_ms':round((time.perf_counter()-start)*1000,1)})
    except Exception as exc:
        publish_result(args.directory,'ready',False,error=str(exc))
        return
    for line in sys.stdin:
        request=json.loads(line)
        sequence=request['sequence']
        try:
            source=(args.directory/request['input']).resolve()
            if not source.is_relative_to(args.directory.resolve()) or source.suffix!='.npy':
                raise ValueError('Invalid inference input path')
            output=ROOT/'debug'/'world-yolo'/f'{os.getpid()}-{sequence}-{time.time_ns()}.json'
            start=time.perf_counter()
            report=detect_frame(np.load(source,allow_pickle=False),model,device,output,request['target'])
            report.update(worker_pid=os.getpid(),model_loads=1,
                          worker_ms=round((time.perf_counter()-start)*1000,1))
            publish_result(args.directory,sequence,True,hits=report)
        except Exception as exc:
            publish_result(args.directory,sequence,False,error=str(exc))


if __name__ == '__main__':
    main()
