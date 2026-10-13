import sys
from pathlib import Path
from unittest.mock import Mock
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'agent'))
from loot_action import pick_loop


class LootLoopTests(unittest.TestCase):
    def result(self,items=None,full=False):
        return {'items':items or [],'inventory_full':full}

    def test_rechecks_after_every_click_and_requires_two_empty(self):
        click = Mock()
        detector = Mock(side_effect=[self.result([{'kind':'pink','box':[100,200,80,30]}]),
            self.result([{'kind':'orange','box':[200,300,80,30]}])]+[self.result()]*2)
        self.assertEqual(pick_loop(Mock(),detector,click,Mock(),Mock()),2)
        self.assertEqual(detector.call_count,4)
        self.assertEqual([c.args for c in click.call_args_list],[(140,215),(240,315)])

    def test_inventory_full_never_clicks(self):
        click = Mock()
        with self.assertRaisesRegex(RuntimeError,'Inventory full'):
            pick_loop(Mock(),Mock(return_value=self.result(full=True)),click,Mock(),Mock())
        click.assert_not_called()

    def test_one_empty_does_not_end_and_orange_text_is_picked(self):
        click = Mock()
        detector = Mock(side_effect=[self.result(), self.result([
            {'kind':'orange_text','box':[100,200,160,30]}]),self.result(),self.result()])
        self.assertEqual(pick_loop(Mock(),detector,click,Mock(),Mock()),1)
        click.assert_called_once_with(180,215)

    def test_frozen_labels_stop(self):
        click = Mock()
        detector = Mock(return_value=self.result([{'kind':'pink','box':[100,200,80,30]}]))
        with self.assertRaisesRegex(RuntimeError,'no progress'):
            pick_loop(Mock(),detector,click,Mock(),Mock())
        self.assertEqual(click.call_count,5)

    def test_stop_after_recognition_prevents_click(self):
        click = Mock()
        guard = Mock(side_effect=[None,RuntimeError('Stopped')])
        with self.assertRaisesRegex(RuntimeError,'Stopped'):
            pick_loop(Mock(),Mock(return_value=self.result([{'kind':'orange','box':[1,2,80,30]}])),
                      click,Mock(),guard)
        click.assert_not_called()
