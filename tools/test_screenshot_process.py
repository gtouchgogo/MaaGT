import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'agent'))
from screenshot_process import ScreenshotProcess
from monitor_protocol import publish_result, result_path


class ScreenshotProtocolTests(unittest.TestCase):
    def temp_directory(self):
        scratch = Path(__file__).resolve().parent.parent/'debug'/'camera'
        scratch.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=scratch)

    def test_worker_error_propagates(self):
        with self.temp_directory() as directory:
            camera = ScreenshotProcess.__new__(ScreenshotProcess)
            camera.directory = Mock(name=directory)
            camera.directory.name = directory
            camera.process = Mock()
            camera.process.poll.return_value = None
            (Path(directory)/'status-ready.json').write_text(json.dumps(
                {'sequence':'ready','ok':False,'error':'native connection failed'}))
            with self.assertRaisesRegex(RuntimeError, 'native connection failed'):
                camera._wait('ready', .1)

    def test_stale_frame_is_not_accepted(self):
        with self.temp_directory() as directory:
            camera = ScreenshotProcess.__new__(ScreenshotProcess)
            camera.directory = Mock()
            camera.directory.name = directory
            camera.process = Mock()
            camera.process.poll.return_value = None
            (Path(directory)/'status-1.json').write_text(json.dumps(
                {'sequence':1,'ok':True}))
            with self.assertRaisesRegex(RuntimeError, 'timed out'):
                camera._wait(2, .02)

    def test_next_response_published_while_previous_is_open(self):
        with self.temp_directory() as directory:
            publish_result(directory, 1, True, hits={'chest':True,'altar':False})
            with result_path(directory, 1).open(encoding='utf-8') as previous:
                publish_result(directory, 2, True, hits={'chest':False,'altar':True})
                self.assertEqual(json.load(previous)['sequence'], 1)
                self.assertEqual(json.loads(result_path(directory, 2).read_text())['sequence'], 2)
            self.assertFalse(list(Path(directory).glob('*.tmp')))

    def test_wait_reads_only_requested_result(self):
        with self.temp_directory() as directory:
            camera = ScreenshotProcess.__new__(ScreenshotProcess)
            camera.directory = Mock()
            camera.directory.name = directory
            camera.process = Mock()
            camera.process.poll.return_value = None
            for sequence in range(1, 101):
                publish_result(directory, sequence, True, hits={'chest':True,'altar':False})
                self.assertEqual(camera._wait(sequence, .1)['sequence'], sequence)


if __name__ == '__main__':
    unittest.main()
