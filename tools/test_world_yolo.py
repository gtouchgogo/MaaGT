import unittest
from world_yolo_detect import select_target


class TargetTests(unittest.TestCase):
    def test_confident_single_target(self):
        box = [100,200,50,60]
        self.assertEqual(select_target([{'name':'chest','score':.95,'box':box}]),box)

    def test_weak_or_wrong_class_not_target(self):
        self.assertIsNone(select_target([{'name':'altar','score':.95,'box':[1,2,3,4]},
                                        {'name':'chest','score':.3,'box':[1,2,3,4]}]))

    def test_multiple_targets_are_uncertain(self):
        self.assertIsNone(select_target([{'name':'chest','score':.95,'box':[1,2,3,4]}]*2))


if __name__ == '__main__':
    unittest.main()
