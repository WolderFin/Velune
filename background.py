"""Windows system tray lifecycle, independent of the OBS server."""
import threading


class BackgroundController:
    def __init__(self, icon_path):
        self.icon_path = icon_path
        self.window = None
        self.tray = None
        self.ready = threading.Event()
        self.quitting = False

    def attach(self, window):
        self.window = window
        window.events.closing += self.on_closing
        window.events.minimized += self.on_minimized

    def start(self):
        import pystray
        from PIL import Image
        with Image.open(self.icon_path) as image:
            tray_image = image.copy()
        self.tray = pystray.Icon(
            'Velune', tray_image, 'Velune — музыка для OBS',
            menu=pystray.Menu(
                pystray.MenuItem('Открыть Velune', self.open_window, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('Выход', self.quit)))
        def setup(icon):
            icon.visible = True
            self.ready.set()
        self.tray.run_detached(setup=setup)

    def hide_to_tray(self):
        if not self.ready.is_set() or self.quitting:
            return False
        self.window.hide()
        return True

    def on_minimized(self):
        self.hide_to_tray()

    def on_closing(self):
        if not self.quitting and self.hide_to_tray():
            return False  # Cancel destruction: the OBS server keeps running.

    def open_window(self, icon=None, item=None):
        if not self.quitting:
            self.window.show()
            self.window.restore()

    def quit(self, icon=None, item=None):
        self.quitting = True
        self.window.destroy()

    def stop(self):
        self.ready.clear()
        if self.tray:
            self.tray.stop()


class DesktopAPI:
    """Only the one desktop action needed by the settings page is exposed."""
    def __init__(self, controller):
        self._controller = controller

    def hide_to_tray(self):
        return self._controller.hide_to_tray()
