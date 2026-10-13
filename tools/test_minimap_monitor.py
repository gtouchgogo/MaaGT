import sys
import threading
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'agent'))
from minimap_monitor import TargetMemory, MinimapMonitor


class MemoryTests(unittest.TestCase):
    def test_two_hits_sticky_and_new_route_reset(self):
        memory = TargetMemory()
        memory.observe({'chest':True,'altar':False})
        self.assertEqual(memory.branch(), 'InsideTargetUncertain')
        memory.observe({'chest':True,'altar':False})
        memory.observe({'chest':False,'altar':False})
        self.assertEqual(memory.branch(), 'InsideChestSeen')
        self.assertFalse(TargetMemory().seen)

    def test_both_targets_are_uncertain(self):
        memory = TargetMemory()
        for _ in range(2):
            memory.observe({'chest':True,'altar':True})
        self.assertEqual(memory.branch(), 'InsideTargetUncertain')

    def test_no_hits_not_empty_brush(self):
        self.assertEqual(TargetMemory().branch(), 'InsideTargetUncertain')

    def test_stop_during_initial_delay(self):
        calls = []
        monitor = MinimapMonitor(lambda:calls.append(1), delay=1)
        monitor.start()
        self.assertEqual(monitor.finish()['checks'], 0)
        self.assertEqual(calls, [])

    def test_worker_error_propagates(self):
        fired = threading.Event()
        def sample():
            fired.set()
            raise ValueError('bad image')
        monitor = MinimapMonitor(sample, delay=0)
        monitor.start()
        self.assertTrue(fired.wait(1))
        with self.assertRaises(RuntimeError):
            monitor.finish()

    def test_stop_discards_inflight_sample(self):
        entered, release = threading.Event(), threading.Event()
        def sample():
            entered.set()
            release.wait(1)
            return {'chest':True,'altar':True}
        monitor = MinimapMonitor(sample, delay=0)
        monitor.start()
        self.assertTrue(entered.wait(1))
        monitor.stop_event.set()
        release.set()
        self.assertEqual(monitor.finish()['checks'], 0)


if __name__ == '__main__':
    unittest.main()
