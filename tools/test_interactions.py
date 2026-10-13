import sys
from pathlib import Path
from unittest.mock import Mock
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'agent'))
from interaction_actions import exit_portal, activate_altar
from minimap_monitor import TargetMemory


class InteractionTests(unittest.TestCase):
    def io(self,zones):
        io=Mock()
        io.observe.side_effect=[{'zone':z} for z in zones]
        io.target.return_value=(900,300)
        return io

    def test_exit_success_without_moving(self):
        io=self.io(['inside','outside','outside'])
        exit_portal(io)
        io.click.assert_called_once_with((900,300))
        self.assertEqual([c.args for c in io.key.call_args_list],[(84,.08)])

    def test_same_point_retry_without_reopening(self):
        io=self.io(['inside']+['inside']*3+['outside']*2)
        exit_portal(io)
        self.assertEqual(io.click.call_count,2)
        self.assertEqual(io.target.call_count,1)
        self.assertEqual(io.key.call_count,1)

    def test_each_direction_opens_clicks_and_verifies(self):
        io=self.io(['inside']+['inside']*15)
        with self.assertRaisesRegex(RuntimeError,'Exit failed'):
            exit_portal(io)
        self.assertEqual([c.args[0] for c in io.key.call_args_list],[84,68,84,83,84,87,84])
        self.assertEqual(io.click.call_count,5)

    def test_loading_uncertain_never_repositions(self):
        io=self.io(['inside']+[None]*12)
        with self.assertRaisesRegex(RuntimeError,'transition uncertain'):
            exit_portal(io)
        self.assertEqual(io.key.call_count,1)

    def test_altar_found_immediately_does_not_move(self):
        io=Mock()
        detect=Mock(return_value={'target':[900,300,80,200]})
        activate_altar(io,detect)
        io.key.assert_not_called()
        io.click.assert_called_once_with((940,400))

    def test_altar_recovery_is_bounded_and_ordered(self):
        io=Mock()
        with self.assertRaisesRegex(RuntimeError,'not located'):
            activate_altar(io,Mock(return_value={'target':None}))
        self.assertEqual([c.args[0] for c in io.key.call_args_list],[83,65,68,87])
        io.click.assert_not_called()

    def test_no_target_requires_valid_checks(self):
        memory=TargetMemory()
        for _ in range(10):
            memory.observe({'chest':False,'altar':False,'valid':False})
        self.assertEqual(memory.branch(),'InsideTargetUncertain')
        for _ in range(6):
            memory.observe({'chest':False,'altar':False,'valid':True})
        self.assertEqual(memory.branch(),'InsideNoTarget')

    def test_one_hit_blocks_empty_exit(self):
        memory=TargetMemory()
        memory.observe({'chest':True,'altar':False,'valid':True})
        for _ in range(10):
            memory.observe({'chest':False,'altar':False,'valid':True})
        self.assertEqual(memory.branch(),'InsideTargetUncertain')
