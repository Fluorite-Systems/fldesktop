from PySide6.QtWidgets import QWidget

from fldesktop.include.superfx import glrender


class SuperFX:
    def __init__(self, comm):
        self.comm = comm
        self.desktop = None
        self.container = None
        self.backend = None

        self.comm.register("superfx", {
            "add_surface":    self.add_surface,
            "remove_surface": self.remove_surface,
            "raise_surface":  self.raise_surface,
            "lower_surface":  self.lower_surface,
            "set_wallpaper":  self.set_wallpaper,
            "invalidate":     self.invalidate,
            "get_container":  lambda: self.container,
            "get_backend":    lambda: self.backend,
        })

        self.comm.subscribe("desktop_size_changed", self.update_size)
        self.create_backend()

    def create_backend(self):
        self.desktop = self.comm.request("desktop", "get_instance")

        self.container = glrender.Container(
            self.desktop, glrender.GlassConfig())
        self.backend = self.container.gl

        self.container.show()
        QWidget.raise_(self.container)

    def update_size(self, *args, **kwargs):
        if self.container is None or self.desktop is None:
            return
        w = self.desktop.width()
        h = self.desktop.height()
        self.container.setGeometry(0, 0, w, h)
        self.backend.setGeometry(0, 0, w, h)

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