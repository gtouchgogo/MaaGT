"""Bounded, read-only route monitoring with sticky target memory."""
import threading
import time


class TargetMemory:
    def __init__(self):
        self.checks = 0
        self.valid_checks = 0
        self.hits = {'chest': 0, 'altar': 0}
        self.seen = set()

    def observe(self, hits):
        self.checks += 1
        if not hits.get('valid',True):
            return
        self.valid_checks += 1
        for name in self.hits:
            if hits[name]:
                self.hits[name] += 1
                if self.hits[name] >= 2:
                    self.seen.add(name)

    def branch(self):
        if self.seen == {'chest'}:
            return 'InsideChestSeen'
        if self.seen == {'altar'}:
            return 'InsideAltarSeen'
        if self.valid_checks >= 6 and not any(self.hits.values()):
            return 'InsideNoTarget'
        return 'InsideTargetUncertain'


class MinimapMonitor:
    def __init__(self, sample, delay=1., interval=.4):
        self.sample = sample
        self.delay, self.interval = delay, interval
        self.stop_event = threading.Event()
        self.memory = TargetMemory()
        self.error = None
        self.worker = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.worker.start()

    def _run(self):
        try:
            if self.stop_event.wait(self.delay):
                return
            while not self.stop_event.is_set():
                start = time.perf_counter()
                hits = self.sample()
                if self.stop_event.is_set():
                    return
                self.memory.observe(hits)
                self.stop_event.wait(max(0, self.interval-(time.perf_counter()-start)))
        except Exception as exc:
            self.error = str(exc)

    def finish(self):
        self.stop_event.set()
        self.worker.join(timeout=5)
        if self.worker.is_alive():
            raise RuntimeError('Minimap worker did not stop; restart the Agent before retrying')
        if self.error:
            raise RuntimeError(f'Minimap monitor failed: {self.error}')
        return {'checks': self.memory.checks, 'valid_checks':self.memory.valid_checks, 'hits': dict(self.memory.hits),
                'seen': sorted(self.memory.seen), 'branch': self.memory.branch()}
