import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent


class WorkflowTests(unittest.TestCase):
    def test_chest_branch_clicks_then_loots_without_replaying_route(self):
        data = json.loads((ROOT/'assets/resource/pipeline/inside_route_clock.json').read_text())
        self.assertEqual(data['InsideChestSeen']['next'], ['FindChestForLoot'])
        self.assertEqual(data['FindChestForLoot']['custom_action'], 'ClickWorldChestOnce')
        self.assertEqual(data['FindChestForLoot']['next'], ['PickChestLoot'])
        self.assertEqual(data['PickChestLoot']['custom_action'], 'PickPinkOrangeLoot')
        self.assertEqual(data['PickChestLoot']['pre_delay'], 0)
        self.assertEqual(data['PickChestLoot']['next'], ['ExitAndReturnToSelector'])
        self.assertEqual(data['InsideAltarSeen']['next'], ['ActivateAltarForLoot'])
        self.assertEqual(data['InsideNoTarget']['next'], ['ExitAndReturnToSelector'])
        self.assertEqual(data['InsideTargetUncertain']['next'], ['AbortUncertainInsideNode'])

    def test_standalone_click_test_still_does_not_loot(self):
        data = json.loads((ROOT/'assets/resource/pipeline/world_chest_click_test.json').read_text())
        self.assertEqual(data['WorldChestClickObservation']['next'], [])


if __name__ == '__main__':
    unittest.main()
