"""Serial offline vision calls, never concurrent Agent RPC."""
import json
import subprocess
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def request_vision(image, worker, extra=(), timeout=45):
    if image.shape != (1080,1920,3):
        raise ValueError('Expected 1920x1080 Maa screenshot')
    folder = ROOT/'debug'/'interaction'
    folder.mkdir(parents=True,exist_ok=True)
    stem = str(time.time_ns())
    source, output = folder/f'{stem}.npy',folder/f'{stem}.json'
    runtime = json.loads((ROOT/'tools/yolo_runtime.json').read_text(encoding='utf-8'))
    np.save(source,image,allow_pickle=False)
    try:
        result = subprocess.run([runtime['python'],str(ROOT/'tools'/worker),
            '--input',str(source),'--output',str(output),*extra],capture_output=True,text=True,
            timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(f'Vision worker failed: {result.stderr[-1200:]}')
        return json.loads(output.read_text(encoding='utf-8'))
    finally:
        source.unlink(missing_ok=True)
