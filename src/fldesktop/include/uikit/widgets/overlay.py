from fldesktop.include.uikit.widgets.base import Widget
from fldesktop.include.widgets.window_overlay import WindowOverlay


class Overlay(Widget):
    def __init__(self, comm, name, attrs):
        super().__init__(comm, name, attrs)
        self.type = "overlay"
        self.ovl = WindowOverlay(self._runner.comm, self._runner.winid)
        self.qwidget = self.ovl.view.cont

        self._runner.comm.request("wm", "add_window_overlay", self._runner.winid, self.ovl)
        
        self._runner.widgets[self.name] = self

        self.ovl.view.close_btn.clicked.connect(self.delete)

    def _cleanup(self):

        self.ovl.close()