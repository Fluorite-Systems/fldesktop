from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor

from fldesktop.include.superfx.container import *


class SuperFX:
    def __init__(self, comm):
        self.comm = comm
        self.desktop = None
        self.container = None
        self.backend = None
        self.config = GlassConfig()

        self.comm.register("superfx", {
            "add_surface": self.add_surface,
            "remove_surface": self.remove_surface,
            "raise_surface": self.raise_surface,
            "lower_surface": self.lower_surface,
            "set_wallpaper": self.set_wallpaper,
            "invalidate": self.invalidate,
            "force_dematerialize": self.force_dematerialize,
            "get_container": lambda: self.container,
            "get_backend": lambda: self.backend,
        })

        self.comm.subscribe("desktop_size_changed", self.update_size)
        self.comm.subscribe("reload_config", self.reconfigure)
        self.create_backend()

        self.reconfigure()

    def create_backend(self):
        self.desktop = self.comm.request("desktop", "get_instance")

        self.container = Container(self.desktop, self.config)

        self.container.show()
        QWidget.raise_(self.container)

    def update_size(self, *args, **kwargs):
        if self.container is None or self.desktop is None:
            return
        w = self.desktop.width()
        h = self.desktop.height()
        self.container.setGeometry(0, 0, w, h)

    def reconfigure(self):

        col = self.comm.request("cfgmgr", "get", "glass-tint-color")
        alpha = self.comm.request("cfgmgr", "get", "glass-tint-alpha")
        bs = self.comm.request("cfgmgr", "get", "glass-blur-strength")

        print(col, alpha, bs)

        self.config.tint = tuple(
            round(c / 255, 3) for c in QColor(col).toTuple()[:3]
        )
        self.config.tint_amount = round(alpha / 255, 3)
        self.config.blur_strength = bs

    def add_surface(self, *args, **kwargs):
        return self.container.add_surface(*args, **kwargs)

    def remove_surface(self, *args, **kwargs):
        return self.container.remove_surface(*args, **kwargs)

    def raise_surface(self, *args, **kwargs):
        return self.container.raise_surface(*args, **kwargs)

    def lower_surface(self, *args, **kwargs):
        return self.container.lower_surface(*args, **kwargs)

    def set_wallpaper(self, *args, **kwargs):
        return self.backend.set_wallpaper(*args, **kwargs)

    def invalidate(self, *args, **kwargs):
        return self.backend.invalidate(*args, **kwargs)

    def force_dematerialize(self):
        return self.container.dematerialize()