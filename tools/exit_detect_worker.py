"""Portal text/ring and fixed title recognition; no input."""
import argparse
import json
import sys
from pathlib import Path
import cv2
import numpy as np


def portal_text(image, legacy):
    path=legacy/'calibration'/'portal_text_sample.png'
    if not path.exists():
        return None
    reference=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),1)[24:61,116:271]
    reference=cv2.cvtColor(reference,cv2.COLOR_BGR2GRAY)
    left,top=400,40
    source=cv2.cvtColor(image[top:750,left:1500],cv2.COLOR_BGR2GRAY)
    best,box=0.,None
    for scale in (.45,.5,.55,.75,.9,1.,1.1):
        template=cv2.resize(reference,None,fx=scale,fy=scale)
        _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(source,template,cv2.TM_CCOEFF_NORMED))
        if score>best:
            best,box=score,[left+x,top+y,template.shape[1],template.shape[0]]
    return box if best>=.85 else None


def inspect(image, vision, legacy):
    if image.shape != (1080,1920,3):
        raise ValueError('Expected 1080p frame')
    large = cv2.resize(image,(3840,2160))
    source = cv2.cvtColor(image[:28,1595:1695],cv2.COLOR_BGR2GRAY)
    scores = {}
    for name in ('inside','outside'):
        ref = cv2.resize(cv2.imdecode(np.fromfile(str(legacy/'calibration'/f'zone_{name}_fixed.png'),dtype=np.uint8),1),(1920,1080))
        template = cv2.cvtColor(ref[1:22,1600:1675],cv2.COLOR_BGR2GRAY)
        scores[name] = float(cv2.minMaxLoc(cv2.matchTemplate(source,template,cv2.TM_CCOEFF_NORMED))[1])
    best = max(scores,key=scores.get)
    other = 'outside' if best == 'inside' else 'inside'
    zone = best if scores[best] >= .85 and scores[best]-scores[other] >= .15 else None
    def half(box):
        return [round(v/2) for v in box] if box else None
    return {'zone':zone,'zone_scores':scores,'text':portal_text(image,legacy) or half(vision.portal_text(large)),
            'ring':half(vision.portal(large)),
            'fixed_point':[round(v/2) for v in vision.points['portal']['point']],
            'inventory_full':vision.inventory_full(large)}


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
    report=inspect(image,Vision(),legacy)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
