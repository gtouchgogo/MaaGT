"""Read selector/entry controls from existing calibration; no input."""
import argparse
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from exit_detect_worker import inspect as inspect_exit


def control(image,vision,name,threshold):
    region=vision.points[name]['region']
    reference=cv2.resize(vision.references[name],(1920,1080))
    if name=='charge':
        dx,dy,w,h=140,66,40,42
    elif name=='boss_ready':
        dx,dy,w,h=72,68,178,40
    else:
        dx,dy,w,h=0,0,region['width'],region['height']
    tx,ty=(region['left']+dx)//2,(region['top']+dy)//2
    template=cv2.cvtColor(reference[ty:ty+h//2,tx:tx+w//2],cv2.COLOR_BGR2GRAY)
    left,top=max(0,region['left']//2-35),max(0,region['top']//2-35)
    source=cv2.cvtColor(image[top:top+region['height']//2+70,left:left+region['width']//2+70],cv2.COLOR_BGR2GRAY)
    _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(source,template,cv2.TM_CCOEFF_NORMED))
    box=[left+x,top+y,template.shape[1],template.shape[0]]
    bright=int(np.count_nonzero(source[y:y+template.shape[0],x:x+template.shape[1]]>180))
    if name=='boss_ready' and bright<100:
        return None,float(score)
    return (box if score>=threshold else None),float(score)


def inspect(image,vision,legacy):
    report=inspect_exit(image,vision,legacy)
    report['entry_controls']={}
    for name,threshold in (('confirm',.87),('boss_ready',.90),('charge',.87)):
        box,score=control(image,vision,name,threshold)
        report['entry_controls'][name]={'box':box,'score':score}
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    runtime=json.loads((root/'tools/yolo_runtime.json').read_text(encoding='utf-8'))
    legacy=Path(runtime['python']).parent.parent.parent
    sys.path.insert(0,str(legacy))
    from vision import Vision
    image=np.load(args.input,allow_pickle=False)
    if image.shape!=(1080,1920,3):
        raise ValueError('Expected 1920x1080 Maa frame')
    report=inspect(image,Vision(),legacy)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
