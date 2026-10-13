"""One inference process per Agent lifetime, serial requests and bounded cleanup."""
import atexit
import json
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
import numpy as np
from monitor_protocol import result_path

ROOT=Path(__file__).resolve().parent.parent
_session=None
_lock=threading.RLock()


class YoloSession:
    def __init__(self):
        folder=ROOT/'debug'/'world-yolo'
        folder.mkdir(parents=True,exist_ok=True)
        self.directory=tempfile.TemporaryDirectory(prefix='session-',dir=folder)
        self.process=None
        self.sequence=0
        env=os.environ.copy()
        env.pop('MAAFW_BINARY_PATH',None)
        try:
            runtime=json.loads((ROOT/'tools/yolo_runtime.json').read_text(encoding='utf-8'))
            self.process=subprocess.Popen([runtime['python'],str(ROOT/'tools/yolo_server.py'),
                '--directory',self.directory.name,'--model',str(ROOT/'assets/resource/model/detect/world_yolo11.pt')],
                stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                text=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            ready=self.wait('ready',60)['hits']
            print('YOLO loaded once and warmed:',json.dumps(ready),flush=True)
        except Exception:
            self.close()
            raise

    def wait(self,sequence,timeout):
        path=result_path(self.directory.name,sequence)
        end=time.perf_counter()+timeout
        while time.perf_counter()<end:
            if path.exists():
                result=json.loads(path.read_text(encoding='utf-8'))
                if result['sequence']!=sequence:
                    raise RuntimeError('YOLO response sequence mismatch')
                if not result['ok']:
                    raise RuntimeError(result['error'])
                return result
            if self.process.poll() is not None:
                raise RuntimeError('Persistent YOLO worker exited')
            time.sleep(.01)
        raise RuntimeError('Persistent YOLO request timed out')

    def detect(self,image,target):
        if image.shape!=(1080,1920,3) or image.dtype!=np.uint8:
            raise ValueError('Expected 1080p uint8 image')
        self.sequence+=1
        source=Path(self.directory.name)/f'{self.sequence}.npy'
        np.save(source,image,allow_pickle=False)
        start=time.perf_counter()
        try:
            request={'sequence':self.sequence,'input':source.name,'target':target}
            self.process.stdin.write(json.dumps(request)+'\n')
            self.process.stdin.flush()
            report=self.wait(self.sequence,15)['hits']
            report['request_ms']=round((time.perf_counter()-start)*1000,1)
            return report
        finally:
            source.unlink(missing_ok=True)

    def close(self):
        if self.process:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=3)
        self.directory.cleanup()


def warm_yolo():
    global _session
    with _lock:
        if _session is None:
            _session=YoloSession()


def detect_yolo(image,target='chest'):
    global _session
    with _lock:
        warm_yolo()
        try:
            return _session.detect(image,target)
        except Exception:
            close_yolo()
            raise


def close_yolo():
    global _session
    with _lock:
        session,_session=_session,None
        if session:
            session.close()


atexit.register(close_yolo)
