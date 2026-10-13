"""Offline YOLO inference worker; never connects to a game or sends input."""
import argparse
import json
import os
from pathlib import Path
import numpy as np


def select_target(detections, name='chest', threshold=.55):
    matches = [d for d in detections if d['name'] == name and d['score'] >= threshold]
    return matches[0]['box'] if len(matches) == 1 else None


def load_detector(path):
    import cv2
    import torch
    from ultralytics import YOLO
    model = YOLO(str(path))
    if set(model.names.values()) != {'chest','altar','portal'}:
        raise ValueError('Unexpected YOLO model classes')
    device = 0 if torch.cuda.is_available() else 'cpu'
    model.predict(np.zeros((775,925,3),dtype=np.uint8),imgsz=1280,conf=.15,
                  iou=.5,device=device,verbose=False)
    return model,device


def detect_frame(image,model,device,output,target='chest'):
    import cv2
    if image.shape != (1080,1920,3) or image.dtype != np.uint8:
        raise ValueError('Expected 1920x1080 uint8 BGR image')
    if target not in ('chest','altar','portal'):
        raise ValueError('Unknown detection target')
    left, top = 500, 75
    result = model.predict(image[top:850,left:1425], imgsz=1280, conf=.15,
                           iou=.5, device=device, verbose=False)[0]
    detections = []
    marked = image.copy()
    for b in result.boxes:
        x1,y1,x2,y2 = b.xyxy[0].cpu().tolist()
        box = [round(left+x1), round(top+y1), round(x2-x1), round(y2-y1)]
        if box[2] <= 0 or box[3] <= 0:
            continue
        name, score = result.names[int(b.cls.item())], float(b.conf.item())
        detections.append({'name':name,'score':score,'box':box})
        x,y,w,h = box
        cv2.rectangle(marked,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.putText(marked,f'{name} {score:.3f}',(x,max(20,y-8)),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,255,0),2)
    raw_path = output.with_name(output.stem+'-raw.png')
    marked_path = output.with_name(output.stem+'-marked.png')
    for path, frame in ((raw_path,image),(marked_path,marked)):
        ok, encoded = cv2.imencode('.png',frame)
        if not ok:
            raise RuntimeError('Cannot encode diagnostic image')
        encoded.tofile(str(path))
    report = {'device':str(device),'detections':detections,
              'target':select_target(detections,target,.65 if target == 'altar' else .55), 'speed_ms':result.speed,
              'marked':str(marked_path), 'raw':str(raw_path)}
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target', choices=('chest','altar','portal'), default='chest')
    args = parser.parse_args()
    settings = (args.output.parent/'yolo-settings').resolve()
    settings.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('YOLO_CONFIG_DIR', str(settings))
    model,device=load_detector(args.model)
    report=detect_frame(np.load(args.input,allow_pickle=False),model,device,args.output,args.target)
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
