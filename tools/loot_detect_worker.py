"""Reuse tested legacy loot rules; this worker never sends game input."""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np


def detect(image, vision, anchor=(960,540)):
    if image.shape != (1080,1920,3) or image.dtype != np.uint8:
        raise ValueError('Expected a 1920x1080 uint8 BGR frame')
    large = cv2.resize(image,(3840,2160))
    groups = {'pink':vision.pink_labels(large), 'orange':vision.orange_labels(large),
              'orange_text':vision.orange_text_labels(large)}
    items = []
    for name, boxes in groups.items():
        for x,y,w,h in boxes:
            box = [round(v/2) for v in (x,y,w,h)]
            bx,by,bw,bh = box
            if (bx+bw/2-anchor[0])**2+(by+bh/2-anchor[1])**2 <= (1920/3)**2:
                items.append({'kind':name,'box':box})
    items.sort(key=lambda item:(item['box'][1],item['box'][0]))
    return {'items':items,'inventory_full':vision.inventory_full(large)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    runtime = json.loads((root/'tools'/'yolo_runtime.json').read_text(encoding='utf-8'))
    legacy = Path(runtime['python']).parent.parent.parent
    sys.path.insert(0,str(legacy))
    from vision import Vision, read_image
    image = np.load(args.input,allow_pickle=False) if args.input.suffix == '.npy' else read_image(args.input)
    report = detect(image,Vision())
    marked = image.copy()
    for item in report['items']:
        x,y,w,h = item['box']
        cv2.rectangle(marked,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.putText(marked,item['kind'],(x,max(20,y-5)),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,255,0),1)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    path = args.output.with_name(args.output.stem+'-marked.png')
    ok,encoded = cv2.imencode('.png',marked)
    if not ok:
        raise RuntimeError('Cannot encode loot diagnostic')
    encoded.tofile(str(path))
    report['marked'] = str(path)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
