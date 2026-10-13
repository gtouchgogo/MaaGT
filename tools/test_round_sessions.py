import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'agent'))
from round_actions import RoundSessions


class RoundSessionTests(unittest.TestCase):
    def test_single_task_has_no_loop(self):
        self.assertEqual(RoundSessions().finish(7), [])

    def test_exactly_three_rounds(self):
        sessions = RoundSessions()
        sessions.begin(7, 3)
        self.assertEqual(sessions.finish(7), ['EnterInsideForRound'])
        self.assertEqual(sessions.finish(7), ['EnterInsideForRound'])
        self.assertEqual(sessions.finish(7), [])
        self.assertEqual(sessions.finish(7), [])

    def test_other_task_cannot_resume_old_session(self):
        sessions = RoundSessions()
        sessions.begin(7, 3)
        self.assertEqual(sessions.finish(8), [])
        sessions.begin(8, 1)
        self.assertEqual(sessions.finish(7), [])
        self.assertEqual(sessions.finish(8), [])

    def test_invalid_limits(self):
        for count in (0, 101, True, 3.5, '3'):
            with self.assertRaises(ValueError):
                RoundSessions().begin(7, count)

    def test_continuous_has_no_round_limit(self):
        sessions = RoundSessions()
        sessions.begin(7, None, continuous=True)
        for _ in range(101):
            self.assertEqual(sessions.finish(7), ['EnterInsideForRound'])
        self.assertEqual(sessions.finish(8), [])
