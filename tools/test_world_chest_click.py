import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'agent'))
from world_chest_action import ClickWorldChestOnce, chest_center


class ClickTests(unittest.TestCase):
    def test_center(self):
        self.assertEqual(chest_center([1241,170,153,185]),(1317,262))

    def test_invalid_box(self):
        for box in ([0,0,0,1],[-1,0,10,10],[1900,0,100,100]):
            with self.assertRaises(ValueError):
                chest_center(box)

    def setup_parts(self):
        context = Mock()
        context.tasker.stopping = False
        context.tasker.controller.post_click.return_value.wait.return_value.succeeded = True
        argv = SimpleNamespace(box=[1241,170,153,185],reco_detail=SimpleNamespace(hit=True))
        return context, argv

    def test_only_one_click(self):
        context,argv = self.setup_parts()
        with patch('world_chest_action.game_is_foreground',return_value=True):
            self.assertTrue(ClickWorldChestOnce().run(context,argv))
        context.tasker.controller.post_click.assert_called_once_with(1317,262)
        context.tasker.controller.post_key_down.assert_not_called()

    def test_stop_or_focus_loss_never_clicks(self):
        for stopped,foreground in ((True,True),(False,False)):
            context,argv = self.setup_parts()
            context.tasker.stopping = stopped
            with patch('world_chest_action.game_is_foreground',return_value=foreground):
                self.assertFalse(ClickWorldChestOnce().run(context,argv))
            context.tasker.controller.post_click.assert_not_called()

    def test_non_hit_never_clicks(self):
        context,argv = self.setup_parts()
        argv.reco_detail.hit = False
        with patch('world_chest_action.game_is_foreground',return_value=True):
            self.assertFalse(ClickWorldChestOnce().run(context,argv))
        context.tasker.controller.post_click.assert_not_called()
