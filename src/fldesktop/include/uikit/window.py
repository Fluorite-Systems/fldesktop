from PySide6.QtWidgets import QWidget, QVBoxLayout

from fldesktop.include.uikit.ui import UI
from fldesktop.include.uikit.dnd import DragFilter, DropFilter


class Window(UI):
    def __init__(self, comm, name, attrs):
        super().__init__(
            comm, name, attrs, {
                "Attr.UI.Window.Package": "none",
                "Attr.UI.Window.Title": "Application",
                "Attr.UI.Window.Width": 600,
                "Attr.UI.Window.Height": 400,
                "Attr.UI.Window.Type": "normal",
            }
        )

        self.callables = {
            "spawn_effect": self.spawn_effect
        }

        self.widget = QWidget()
        self.qlayout = QVBoxLayout(self.widget)

        self.drag_filter = DragFilter(self.widget)
        self.drop_filter = DropFilter(self.widget)
    
        # Create a window
        self.winid, self.on_close = self.comm.request(
            "wm", "create_window", self.attrs["Attr.UI.Window.Title"],
            self.widget, self.get_win_icon(),
            self.attrs["Attr.UI.Window.Package"],
            (self.attrs["Attr.UI.Window.Width"],
             self.attrs["Attr.UI.Window.Height"]),
            self.attrs["Attr.UI.Window.Type"]
        )

        self.on_close.connect(lambda: self.event(type="close"))
    

    def get_win_icon(self):

        pkgs = self.comm.request("pkgmgr", "get_apps")

        for name, value in pkgs.items():
            if name == self.attrs["Attr.UI.Window.Package"]:
                return value.icon

        return self.comm.request("iconmgr", "get", "application-generic")

    def apply_attrs(self):
        super().apply_attrs()

    def delete(self):

        self.comm.request("wm", "close_window", self.winid)

    def spawn_effect(self, effect: str = "confetti"):

        if effect == "confetti":
            self.comm.request("wm", "spawn_effect", self.winid, "confetti")