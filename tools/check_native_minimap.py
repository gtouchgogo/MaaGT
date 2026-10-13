"""Exercise real native Maa recognition on synthetic frames, without game input."""
import sys
import ctypes
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'agent'))
from screenshot_worker import NativeMinimapRecognizer
from maa.controller import CustomController
from maa.buffer import ImageBuffer
from maa.library import Library
from maa.define import MaaImageBufferHandle, MaaSize, MaaBool


class OfflineController(CustomController):
    def connect(self):
        return True

    def request_uuid(self):
        return 'offline-minimap-check'

    def screencap(self):
        return np.zeros((1080,1920,3), dtype=np.uint8)


def main():
    print('Creating offline controller', flush=True)
    camera = OfflineController()
    print('Connecting offline controller', flush=True)
    assert camera.post_connection().wait().succeeded
    print('Loading resource and binding recognizer', flush=True)
    recognizer = NativeMinimapRecognizer(camera)
    print('Recognizing blank frame', flush=True)
    blank = np.zeros((1080,1920,3), dtype=np.uint8)
    blank_result=recognizer.detect(blank)
    assert not blank_result['chest'] and not blank_result['altar'] and not blank_result['valid']
    root = Path(__file__).resolve().parent.parent
    for name in ('chest','altar'):
        template = ImageBuffer()
        encoded = (root/'assets'/'resource'/'image'/f'minimap_{name}.png').read_bytes()
        data = ctypes.create_string_buffer(encoded)
        decode = Library.framework().MaaImageBufferSetEncoded
        decode.argtypes = [MaaImageBufferHandle, ctypes.c_void_p, MaaSize]
        decode.restype = MaaBool
        assert decode(template._handle, ctypes.cast(data,ctypes.c_void_p), len(encoded))
        image = blank.copy()
        pixels = template.get()
        h,w = pixels.shape[:2]
        image[100:100+h,1700:1700+w] = pixels[:,:,:3]
        result = recognizer.detect(image)
        assert result[name], (name,result)
        print(name, result)
    print('Real native Maa offline recognition passed; no game input sent.')


if __name__ == '__main__':
    main()
