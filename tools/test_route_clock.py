import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'agent'))
from route_clock import replay


class ClockTests(unittest.TestCase):
    def run_route(self, stop_at=None, fail=False):
        now = [0.]
        calls = []
        def send(key, down):
            calls.append((round(now[0],3),key,down))
            now[0] += .03
            return not (fail and down)
        def sleep(t):
            now[0] += t
        edges = [(0,68,True),(.1,87,True),(.5,68,False),(1,87,False)]
        result = replay(edges, send, lambda: stop_at is not None and now[0]>=stop_at,
                        clock=lambda:now[0], sleep=sleep)
        return result, calls

    def test_overhead_not_added_to_each_interval(self):
        ok, calls = self.run_route()
        self.assertTrue(ok)
        self.assertEqual([t for t,_,_ in calls], [0,.1,.5,1])

    def test_stop_releases_all_held_keys(self):
        ok, calls = self.run_route(stop_at=.2)
        self.assertFalse(ok)
        self.assertEqual([(k,d) for _,k,d in calls[-2:]], [(68,False),(87,False)])

    def test_failed_down_still_released(self):
        with self.assertRaises(RuntimeError):
            self.run_route(fail=True)


if __name__ == '__main__':
    unittest.main()
