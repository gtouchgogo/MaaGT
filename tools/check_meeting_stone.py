"""Offline translated-frame regression for the local 1080p stone template."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from stone_detect_worker import meeting_stone

ROOT=Path(__file__).resolve().parent.parent
runtime=json.loads((ROOT/'tools/yolo_runtime.json').read_text(encoding='utf-8'))
legacy=Path(runtime['python']).parent.parent.parent
sys.path.insert(0,str(legacy))
from vision import read_image


def main():
    image=read_image(ROOT/'debug/meeting-stone-regression.png')
    template=ROOT/'assets/resource/image/meeting_stone.png'
    box,score=meeting_stone(image,template)
    assert box is not None,(box,score)
    for dx,dy in ((80,0),(-60,40),(30,-25)):
        shifted=np.roll(np.roll(image,dy,axis=0),dx,axis=1)
        found,_=meeting_stone(shifted,template)
        assert found==[box[0]+dx,box[1]+dy,box[2],box[3]],(dx,dy,found)
    negative=cv2.resize(read_image(legacy/'calibration/zone_inside_fixed.png'),(1920,1080))
    assert meeting_stone(negative,template)[0] is None
    print('Local stone, three translations and inside negative passed:',box,score)


if __name__ == '__main__':
    main()
