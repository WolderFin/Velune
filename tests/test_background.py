import unittest
from unittest.mock import Mock
from background import BackgroundController


class BackgroundTests(unittest.TestCase):
    def setUp(self):
        self.controller = BackgroundController('static/velune.png')
        self.controller.window = Mock()

    def test_window_can_close_if_tray_is_not_ready(self):
        self.assertIsNone(self.controller.on_closing())
        self.assertFalse(self.controller.hide_to_tray())
        self.controller.window.hide.assert_not_called()

    def test_closing_and_minimizing_hide_without_destroying(self):
        self.controller.ready.set()
        self.assertFalse(self.controller.on_closing())
        self.controller.on_minimized()
        self.assertEqual(self.controller.window.hide.call_count, 2)
        self.controller.window.destroy.assert_not_called()

    def test_open_restores_window_and_quit_allows_destruction(self):
        self.controller.ready.set()
        self.controller.open_window()
        self.controller.window.show.assert_called_once()
        self.controller.window.restore.assert_called_once()
        self.controller.quit()
        self.controller.window.destroy.assert_called_once()
        self.assertIsNone(self.controller.on_closing())
        self.assertFalse(self.controller.hide_to_tray())

    def test_shutdown_removes_tray(self):
        self.controller.tray = Mock()
        self.controller.ready.set()
        self.controller.stop()
        self.controller.tray.stop.assert_called_once()
        self.assertFalse(self.controller.ready.is_set())


if __name__ == '__main__':
    unittest.main()
