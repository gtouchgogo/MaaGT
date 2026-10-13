"""Standalone native Maa screenshot/recognition worker; never sends input."""
import json
import sys
import shutil
import tempfile
from pathlib import Path
import numpy as np
from maa.controller import Win32Controller
from maa.library import Library
from maa.resource import Resource
from maa.tasker import Tasker
from monitor_protocol import publish_result


class NativeMinimapRecognizer:
    def __init__(self, camera):
        self.resource = Resource()
        root = Path(__file__).resolve().parent.parent
        # Load only the two tested templates, not boilerplate OCR/custom tasks.
        scratch = root/'debug'/'camera'
        scratch.mkdir(parents=True, exist_ok=True)
        self.bundle = tempfile.TemporaryDirectory(prefix='recognition-', dir=scratch)
        bundle = Path(self.bundle.name)
        (bundle/'pipeline').mkdir()
        (bundle/'image').mkdir()
        source = root/'assets'/'resource'
        definitions = json.loads((source/'pipeline'/'minimap_test.json').read_text(encoding='utf-8-sig'))
        selected = {}
        for node in ('FindMinimapChest','FindMinimapAltar'):
            definition = dict(definitions[node])
            definition.update(action='DoNothing', next=[])
            selected[node] = definition
            templates = definition['template']
            for relative in [templates] if isinstance(templates,str) else templates:
                original = (source/'image'/relative).resolve()
                if not original.is_relative_to((source/'image').resolve()):
                    raise ValueError('Template must be inside resource/image')
                destination = bundle/'image'/relative
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(original,destination)
        (bundle/'pipeline'/'minimap.json').write_text(json.dumps(selected),encoding='utf-8')
        if not self.resource.post_bundle(bundle).wait().succeeded:
            raise RuntimeError('Cannot load native minimap resource bundle')
        self.tasker = Tasker()
        if not self.tasker.bind(self.resource, camera):
            raise RuntimeError('Cannot bind native minimap recognizer')
        self.nodes = {}
        for name, node in (('chest','FindMinimapChest'),('altar','FindMinimapAltar')):
            definition = self.resource.get_node_object(node)
            if definition is None or str(definition.recognition.type) != 'TemplateMatch':
                raise RuntimeError(f'Missing TemplateMatch node: {node}')
            self.nodes[name] = definition.recognition

    def detect(self, image):
        hits = {}
        for name, recognition in self.nodes.items():
            detail = self.tasker.post_recognition(recognition.type, recognition.param, image).wait().get()
            if detail is None or not detail.nodes or detail.nodes[0].recognition is None:
                raise RuntimeError(f'Native recognition failed: {name}')
            hits[name] = bool(detail.nodes[0].recognition.hit)
        panel=image[50:337,1600:1901].astype(np.int16)
        b,g,r=panel[:,:,0],panel[:,:,1],panel[:,:,2]
        purple=(r>75)&(b>80)&(r>g*1.15)&(b>g*1.2)&((np.max(panel,axis=2)-np.min(panel,axis=2))>40)
        gold=(r>90)&(g>70)&(r>b*1.3)&(g>b*1.2)
        hits['valid']=bool(np.count_nonzero(purple)>=4 and np.count_nonzero(gold)>=12)
        return hits


def main():
    hwnd, directory = sys.argv[1:]
    folder = Path(directory)
    sequence = 'ready'

    def status(ok, error='', hits=None):
        publish_result(folder, sequence, ok, error, hits)

    try:
        if Library.is_agent_server():
            raise RuntimeError('Screenshot worker must load native MaaFramework, not AgentServer')
        camera = Win32Controller(int(hwnd), screencap_method=2, mouse_method=4, keyboard_method=4)
        if not camera.post_connection().wait().succeeded:
            raise RuntimeError('Native Maa camera connection failed; rescan the game window')
        if not camera.set_screenshot_target_short_side(1080):
            raise RuntimeError('Cannot set capture size')
        recognizer = NativeMinimapRecognizer(camera)
        status(True)
        for line in sys.stdin:
            sequence = int(line.strip())
            if not camera.post_screencap().wait().succeeded:
                raise RuntimeError('Native Maa capture failed')
            image = camera.cached_image
            if image.shape != (1080,1920,3) or image.dtype != np.uint8:
                raise RuntimeError(f'Unexpected capture format: {image.shape}, {image.dtype}')
            status(True, hits=recognizer.detect(image))
    except Exception as exc:
        status(False, str(exc))


if __name__ == '__main__':
    main()
