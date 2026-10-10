from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget

from fldesktop.include.superfx.glrender import (
    PROP_ENABLE_GLOW,
    PROP_HOVER_MAT,
    PROP_LAYER,
    PROP_NEVER_MAT,
    PROP_TINT_SCALE,
)


class Surface(QWidget):
    def __init__(self, comm, tint=1, size=(400, 300), parent=None,
                 z=1.0, glass=True, layer=None,
                 hover_materialize=False,
                 never_materialize=False,
                 auto_attach=True):
        super().__init__(parent)

        self.comm = comm
        self.tint = int(tint)

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True)

        if isinstance(size, (tuple, list)) and len(size) == 2:
            self.resize(int(size[0]), int(size[1]))
        else:
            self.resize(size)

        self._z = float(z)
        self._glass = bool(glass)
        self._layer = layer if layer in (None, "bottom", "top") else None
        self._hover_materialize = bool(hover_materialize)
        self._never_materialize = bool(never_materialize)

        self._surface = None
        self._user_hidden = False
        self._focus_target = None

        if auto_attach:
            QTimer.singleShot(0, self._do_attach)

    def _apply_props(self):
        self.setProperty(PROP_LAYER, self._layer)
        self.setProperty(PROP_HOVER_MAT, self._hover_materialize)
        self.setProperty(PROP_NEVER_MAT, self._never_materialize)
        if self.property(PROP_ENABLE_GLOW) is None:
            self.setProperty(PROP_ENABLE_GLOW, True)
        if self.property(PROP_TINT_SCALE) is None:
            self.setProperty(PROP_TINT_SCALE, 1.0)

    def _do_attach(self):
        if self._surface is not None:
            return
        if self._user_hidden:
            return
        if not self._alive():
            return
        self._apply_props()
        self._surface = self.comm.request(
            "superfx", "add_surface",
            self, z=self._z, glass=self._glass)
        if self._surface is not None:
            self._on_attach()

    def attach(self, z=None, glass=None):
        if z is not None:
            self._z = float(z)
        if glass is not None:
            self._glass = bool(glass)
        self._user_hidden = False
        self._do_attach()
        return self._surface

    def detach(self):
        if self._surface is None:
            return
        try:
            self.comm.request("superfx", "remove_surface", self)
        except Exception:
            pass
        self._surface = None
        self._on_detach()

    def surface(self):
        return self._surface

    def attached(self):
        return self._surface is not None

    def show(self):
        self._user_hidden = False
        if self._surface is None:
            self._do_attach()
        super().show()

    def hide(self):
        self._user_hidden = True
        if self._surface is not None:
            self.detach()
        super().hide()

    def raise_(self):
        super().raise_()
        if self._surface is None:
            return
        parent = self.parent()
        if parent is not None and getattr(parent, "_restacking", False):
            return
        try:
            self.comm.request("superfx", "raise_surface", self)
        except Exception:
            pass

    def lower(self):
        super().lower()
        if self._surface is None:
            return
        parent = self.parent()
        if parent is not None and getattr(parent, "_restacking", False):
            return
        try:
            self.comm.request("superfx", "lower_surface", self)
        except Exception:
            pass

    def set_glass(self, glass):
        self._glass = bool(glass)

    def glass(self):
        return self._glass

    def layer(self):
        return self._layer

    def set_glow_enabled(self, enabled):
        self.setProperty(PROP_ENABLE_GLOW, bool(enabled))
        self.update()

    def glow_enabled(self):
        v = self.property(PROP_ENABLE_GLOW)
        return True if v is None else bool(v)

    def set_tint_amount_scale(self, scale):
        self.setProperty(PROP_TINT_SCALE, float(scale))
        self.update()

    def tint_amount_scale(self):
        v = self.property(PROP_TINT_SCALE)
        try:
            return float(v) if v is not None else 1.0
        except (TypeError, ValueError):
            return 1.0

    def set_hover_materialize(self, enabled):
        self._hover_materialize = bool(enabled)
        self.setProperty(PROP_HOVER_MAT, self._hover_materialize)

    def hover_materialize(self):
        return self._hover_materialize

    def set_never_materialize(self, enabled):
        self._never_materialize = bool(enabled)
        self.setProperty(PROP_NEVER_MAT, self._never_materialize)

    def never_materialize(self):
        return self._never_materialize
    
    def subscribe(self, signal, action):
        self.comm.subscribe(signal, action)

    def unsubscribe(self, action):
        self.comm.unsubscribe(action)

    def emit(self, signal, *args, **kwargs):
        self.comm.emit(signal, *args, **kwargs)

    def set_focus_target(self, widget):
        self._focus_target = widget

    def give_focus(self):
        target = self._focus_target or self
        try:
            target.setFocus(Qt.FocusReason.MouseFocusReason)
        except (RuntimeError, SystemError):
            pass
        self.on_activate()

    def _on_attach(self):
        pass

    def _on_detach(self):
        pass

    def _on_close(self):
        pass

    def on_activate(self):
        pass

    def _alive(self):
        try:
            self.width()
            return True
        except (RuntimeError, SystemError):
            return False

    def closeEvent(self, event):
        self._on_close()
        self._user_hidden = True
        self.detach()
        super().closeEvent(event)