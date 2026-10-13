import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'agent'))
import route_action


class IntegrationTests(unittest.TestCase):
    def setup_parts(self):
        context = Mock()
        context.tasker.stopping = False
        context.clone.return_value.run_recognition.return_value = SimpleNamespace(hit=False)
        camera = Mock()
        camera.detect.return_value = {'chest':False,'altar':False}
        camera.post_connection.return_value.wait.return_value.succeeded = True
        camera.post_screencap.return_value.wait.return_value.succeeded = True
        camera.set_screenshot_target_short_side.return_value = True
        user32 = Mock()
        user32.GetForegroundWindow.return_value = 123
        def title(hwnd, buffer, size):
            buffer.value = 'Last Epoch'
        user32.GetWindowTextW.side_effect = title
        argv = SimpleNamespace(custom_action_param=json.dumps({'monitor_minimap':True}),
                               node_name='InsideRouteClock')
        return context, camera, user32, argv

    def test_both_recognizers_and_non_hit_detail(self):
        context, camera, user32, argv = self.setup_parts()
        samples = []
        class FakeMonitor:
            error = None
            worker = Mock(is_alive=Mock(return_value=False))
            def __init__(self, sample):
                self.sample = sample
            def start(self):
                samples.append(self.sample())
            def finish(self):
                return {'branch':'InsideTargetUncertain'}
        with patch.object(route_action.ctypes,'WinDLL',return_value=user32), \
             patch.object(route_action,'ScreenshotProcess',return_value=camera), \
             patch.object(route_action,'MinimapMonitor',FakeMonitor), \
             patch.object(route_action,'replay',return_value=True):
            self.assertTrue(route_action.ReplayRecordedRoute().run(context, argv))
        self.assertEqual(samples, [{'chest':False,'altar':False}])
        context.clone.assert_not_called()
        camera.detect.assert_called_once()
        context.override_next.assert_called_once_with('InsideRouteClock',['InsideTargetUncertain'])
        context.tasker.controller.post_screencap.assert_not_called()

    def test_camera_connection_failure_before_movement(self):
        context, camera, user32, argv = self.setup_parts()
        with patch.object(route_action.ctypes,'WinDLL',return_value=user32), \
             patch.object(route_action,'ScreenshotProcess',side_effect=RuntimeError('camera connection failed')), \
             patch.object(route_action,'replay') as replay:
            self.assertFalse(route_action.ReplayRecordedRoute().run(context, argv))
            replay.assert_not_called()


if __name__ == '__main__':
    unittest.main()
