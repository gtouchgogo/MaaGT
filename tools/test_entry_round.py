import sys
import json
from pathlib import Path
from unittest.mock import Mock
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'agent'))
from entry_action import enter_inside


def report(ready=False,charge=False,confirm=False,zone='outside'):
    return {'zone':zone,'entry_controls':{
        name:{'box':[100,200,80,30] if value else None}
        for name,value in (('boss_ready',ready),('charge',charge),('confirm',confirm))}}


class EntryTests(unittest.TestCase):
    def io(self,zones):
        io=Mock()
        io.observe.side_effect=[{'zone':z} for z in zones]
        return io

    def test_ready_does_not_charge(self):
        io=self.io(['inside','inside'])
        observe=Mock(side_effect=[report(ready=True,charge=True),report(confirm=True)])
        enter_inside(io,observe)
        io.click.assert_called_once_with((140,215),button=1)
        self.assertEqual(observe.call_count,1)

    def test_charges_until_ready_then_enters(self):
        io=self.io([None,'inside','inside'])
        observe=Mock(side_effect=[report(charge=True),report(ready=True),report(confirm=True)])
        enter_inside(io,observe)
        self.assertEqual(io.click.call_count,2)
        self.assertEqual(io.click.call_args.kwargs,{'button':1})

    def test_charge_limit(self):
        io=Mock()
        with self.assertRaisesRegex(RuntimeError,'charge limit'):
            enter_inside(io,Mock(return_value=report(charge=True)),max_charges=2)
        self.assertEqual(io.click.call_count,2)

    def test_unknown_ui_does_not_click(self):
        io=Mock()
        with self.assertRaises(RuntimeError):
            enter_inside(io,Mock(return_value=report()))
        io.click.assert_not_called()

    def test_unconfirmed_transition_does_not_start_route(self):
        io=Mock()
        io.observe.return_value={'zone':None}
        with self.assertRaisesRegex(RuntimeError,'not confirmed'):
            enter_inside(io,Mock(return_value=report(confirm=True)))
        self.assertEqual(io.click.call_count,1)

    def test_full_round_has_no_loop(self):
        root=Path(__file__).resolve().parent.parent
        data=json.loads((root/'assets/resource/pipeline/full_round.json').read_text())
        outside=json.loads((root/'assets/resource/pipeline/outside_return.json').read_text())
        self.assertEqual(data['FullRoundTest']['next'],['EnterInsideForRound'])
        self.assertEqual(data['InsideRouteForRound']['pre_delay'],0)
        self.assertEqual(outside['SelectorRoundComplete']['next'],['FinishRoundSession'])
