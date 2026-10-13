"""Keep native Maa screenshot creation outside the AgentServer process."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from monitor_protocol import result_path


class ScreenshotProcess:
    def __init__(self, hwnd):
        self.process = None
        scratch = Path(__file__).resolve().parent.parent/'debug'/'camera'
        scratch.mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix='maagt-camera-', dir=scratch)
        self.sequence = 0
        env = os.environ.copy()
        env.pop('MAAFW_BINARY_PATH', None)
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name('screenshot_worker.py')),
                 str(hwnd), self.directory.name],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                text=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            self._wait('ready', 8)
        except Exception:
            self.close()
            raise

    def _wait(self, sequence, timeout):
        deadline = time.perf_counter()+timeout
        status = result_path(self.directory.name, sequence)
        while time.perf_counter() < deadline:
            if status.exists():
                result = json.loads(status.read_text(encoding='utf-8'))
                if result.get('sequence') == sequence:
                    if not result['ok']:
                        raise RuntimeError(result['error'])
                    return result
            if self.process.poll() is not None:
                raise RuntimeError('Native Maa screenshot process exited unexpectedly')
            time.sleep(.01)
        raise RuntimeError('Native Maa screenshot process timed out')

    def detect(self):
        self.sequence += 1
        self.process.stdin.write(f'{self.sequence}\n')
        self.process.stdin.flush()
        result = self._wait(self.sequence, 3)
        hits = result.get('hits')
        if not isinstance(hits, dict) or any(type(hits.get(k)) is not bool for k in ('chest','altar')):
            raise RuntimeError('Invalid native minimap result')
        return hits

    def close(self):
        if self.process:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=2)
        self.directory.cleanup()
