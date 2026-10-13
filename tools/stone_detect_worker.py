"""Recognize selector UI and stone core on 1080p frames; never sends input."""
import argparse
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from exit_detect_worker import inspect as inspect_exit


def meeting_stone(image,path):
    reference=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),1)
    if reference is None:
        raise ValueError('Cannot read meeting_stone.png')
    h,w=reference.shape[:2]
    # Exclude the floor rim, player health bar/name and most surrounding scenery.
    core=reference[max(0,round(h*.05)):round(h*.73),round(w*.22):round(w*.75)]
    if min(core.shape[:2])<10:
        raise ValueError('meeting_stone.png is too small')
    core=cv2.cvtColor(core,cv2.COLOR_BGR2GRAY)
    left,top=350,80
    source=cv2.cvtColor(image[top:725,left:1425],cv2.COLOR_BGR2GRAY)
    best,box=0.,None
    for scale in (.9,1.,1.1):
        template=cv2.resize(core,None,fx=scale,fy=scale)
        _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(source,template,cv2.TM_CCOEFF_NORMED))
        if score>best:
            best,box=score,[left+x,top+y,template.shape[1],template.shape[0]]
    return (box if best>=.82 else None),float(best)


def inspect(image,vision,legacy):
    report=inspect_exit(image,vision,legacy)
    matches={}
    for name in ('charge','boss_ready'):
        region=vision.points[name]['region']
        x=max(0,region['left']//2-35)
        y=max(0,region['top']//2-35)
        w=region['width']//2+70
        h=region['height']//2+70
        source=cv2.cvtColor(image[y:y+h,x:x+w],cv2.COLOR_BGR2GRAY)
        # Crop after resizing so odd-pixel source offsets do not shift glyph sampling.
        reference=cv2.resize(vision.references[name],(1920,1080))
        dx,dy,tw,th=(140,66,40,42) if name=='charge' else (72,68,178,40)
        tx,ty=(region['left']+dx)//2,(region['top']+dy)//2
        template=cv2.cvtColor(reference[ty:ty+th//2,tx:tx+tw//2],cv2.COLOR_BGR2GRAY)
        matches[name]=float(cv2.minMaxLoc(cv2.matchTemplate(source,template,cv2.TM_CCOEFF_NORMED))[1])
    report['selector_open']=any(score>=.87 for score in matches.values())
    report['selector_scores']=matches
    report['stone']=None
    if report['selector_open']:
        return report
    local=Path(__file__).resolve().parent.parent/'assets/resource/image/meeting_stone.png'
    if local.exists():
        report['stone'],report['stone_score']=meeting_stone(image,local)
        report['stone_template']='meeting_stone.png:core'
        return report
    if vision.stone_core is not None:
        source=cv2.cvtColor(image[100:725,350:1425],cv2.COLOR_BGR2GRAY)
        best,box=0.,None
        for scale in (.45,.5,.55):
            template=cv2.resize(vision.stone_core,None,fx=scale,fy=scale)
            _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(source,template,cv2.TM_CCOEFF_NORMED))
            if score>best:
                best,box=score,[350+x,100+y,template.shape[1],template.shape[0]]
        report['stone']=box if best>=.82 else None
        report['stone_score']=best
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
    report=inspect(np.load(args.input,allow_pickle=False),Vision(),legacy)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
