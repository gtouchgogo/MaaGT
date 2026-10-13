import json
import sys
from pathlib import Path
from unittest.mock import Mock,patch
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'agent'))
from outside_action import route_parts,open_selector,ReturnOutsideToSelector


class OutsideTests(unittest.TestCase):
    def test_actual_route_parts(self):
        root=Path(__file__).resolve().parent.parent
        record=json.loads((root/'routes/outside.json').read_text())
        edges,point,pause=route_parts(record)
        self.assertEqual(len(edges),4)
        self.assertEqual(point,(971,377))
        self.assertAlmostEqual(edges[-1][0],2.896045)
        self.assertEqual(pause,0)

    def report(self,opened=False,stone=None,zone='outside'):
        return {'selector_open':opened,'stone':stone,'zone':zone}

    def test_fixed_click_before_any_detection(self):
        io=Mock()
        parent=Mock()
        parent.attach_mock(io.click,'click')
        observe=Mock(return_value=self.report(True))
        parent.attach_mock(observe,'observe')
        open_selector(io,observe,(971,377))
        io.click.assert_called_once_with((971,377))
        self.assertEqual([c[0] for c in parent.mock_calls],['click','observe'])

    def test_missed_click_reacquires_core(self):
        io=Mock()
        observe=Mock(side_effect=[self.report(stone=[700,200,100,80]),self.report(True)])
        open_selector(io,observe,(971,377))
        self.assertEqual([c.args[0] for c in io.click.call_args_list],[(971,377),(750,240)])

    def test_no_extra_click_after_open_confirmed(self):
        io=Mock()
        open_selector(io,Mock(return_value=self.report(True)),(971,377))
        io.click.assert_called_once_with((971,377))

    def test_retries_bounded(self):
        io=Mock()
        with self.assertRaisesRegex(RuntimeError,'three core retries'):
            open_selector(io,Mock(return_value=self.report(stone=[700,200,100,80])),(971,377))
        self.assertEqual(io.click.call_count,4)

    def test_unknown_zone_after_first_click_prevents_retry(self):
        io=Mock()
        with self.assertRaises(RuntimeError):
            open_selector(io,Mock(return_value=self.report(zone=None)),(971,377))
        io.click.assert_called_once_with((971,377))

    def test_already_open_before_route_never_moves_or_clicks(self):
        io=Mock()
        report={'selector_open':True,'inventory_full':False,'zone':'outside'}
        with patch('outside_action.InteractionIO',return_value=io), \
             patch('outside_action.request_vision',return_value=report), \
             patch('outside_action.replay') as playback:
            self.assertTrue(ReturnOutsideToSelector().run(Mock(),Mock()))
            playback.assert_not_called()
        io.click.assert_not_called()

    def test_initial_zone_uncertain_never_replays(self):
        io=Mock()
        report={'selector_open':False,'inventory_full':False,'zone':None}
        with patch('outside_action.InteractionIO',return_value=io), \
             patch('outside_action.request_vision',return_value=report), \
             patch('outside_action.replay') as playback:
            self.assertFalse(ReturnOutsideToSelector().run(Mock(),Mock()))
            playback.assert_not_called()
