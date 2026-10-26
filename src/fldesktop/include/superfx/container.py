from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtWidgets import QApplication, QWidget

from dataclasses import dataclass
import logging


PROP_LAYER = "compositor.layer"
PROP_LAYER_LOCKED = "compositor.layer_locked"
PROP_ENABLE_GLOW = "compositor.enable_glow"
PROP_TINT_SCALE = "compositor.tint_amount_scale"
PROP_TINT_COLOR = "compositor.tint_color"
PROP_HOVER_MAT = "compositor.materialize_on_hover"
PROP_NEVER_MAT = "compositor.never_materialize"
PROP_OPACITY = "compositor.opacity"
PROP_CONTENT_STATIC = "compositor.content_static"

DEFAULT_LAYER = 1.0


@dataclass
class GlassConfig:
    tint: tuple = (0.1, 0.1, 0.1)
    tint_amount: float = 0.4
    blur_strength: float = 0.3

    shadow_offset: tuple = (0.004, 0.004)
    shadow_spread: float = 0.014
    shadow_alpha: float = 0.55

    wave_strength: float = 0.30
    wave_scale: float = 2.0
    wave_angle: float = -0.5

    chroma: float = 0.0015
    lens: float = 0.012
    noise: float = 0.014

    rim_strength: float = 0.65
    sparkle_strength: float = 0.85
    edge_offset: float = 0.012
    edge_sensitivity: float = 1.0


def _alive(w):
    if w is None:
        return False
    try:
        w.width()
        return True
    except (RuntimeError, SystemError):
        return False


def _prop(w, name):
    try:
        return w.property(name)
    except (RuntimeError, SystemError):
        return None


def _q_raise(w):
    QWidget.raise_(w)


def _q_show(w):
    QWidget.show(w)


def _app_closing():
    app = QApplication.instance()
    return app is None or app.closingDown()


def _paintable(w):
    if not _alive(w):
        return False
    try:
        if not w.isVisible():
            return False
        if not w.testAttribute(Qt.WidgetAttribute.WA_WState_Polished):
            return False
    except (RuntimeError, SystemError):
        return False
    return True


def _coerce_layer(v):
    if v is None:
        return DEFAULT_LAYER
    if isinstance(v, str):
        if v == "bottom":
            return 0.0
        if v == "top":
            return 2.0
        return DEFAULT_LAYER
    try:
        return float(v)
    except (TypeError, ValueError):
        return DEFAULT_LAYER


class Container(QWidget):
    def __init__(self, desktop, config=None):
        super().__init__(desktop)
        if config is None:
            config = GlassConfig()

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.setGeometry(0, 0, desktop.width(), desktop.height())

        try:
            from fldesktop.include.superfx.glrender import GLRender
            self.renderer = GLRender(self, config)
        except Exception as e:
            logging.warning(f"GLRender failed: {e}")
            from fldesktop.include.superfx.simplerender import SimpleRender
            self.renderer = SimpleRender(self, config)

        self.renderer.setGeometry(0, 0, self.width(), self.height())
        _q_show(self.renderer)
        _q_raise(self.renderer)

        self._materialized = None
        self._materialized_by_hover = False
        self._restacking = False

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._on_about_to_quit)

    def _on_about_to_quit(self):
        try:
            if _alive(self.renderer):
                self.renderer.close()
        except (RuntimeError, SystemError):
            pass

    def add_surface(self, w, z=None, glass=None, layer=None, locked=None):
        if not _alive(w):
            return None

        try:
            gp = w.mapToGlobal(QPoint(0, 0))
        except (RuntimeError, SystemError):
            gp = None

        try:
            w.setParent(self)
            w.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground, True)
            w.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            if gp is not None:
                try:
                    w.move(self.mapFromGlobal(gp))
                except (RuntimeError, SystemError):
                    pass
            _q_show(w)
        except (RuntimeError, SystemError):
            return None

        z = z if z is not None else getattr(w, "_z", 1.0)
        glass = glass if glass is not None else getattr(w, "_glass", True)
        reg = self.renderer.register(w, z=z, glass=glass,
                                     layer=layer, locked=locked)
        self._restack()
        return reg

    def remove_surface(self, w):
        if w is self._materialized:
            self._materialized = None
            self._materialized_by_hover = False
            self.renderer._materialized_widget = None

        self.renderer.unregister(w)

        if _app_closing():
            return

        try:
            if _alive(w) and w.parentWidget() is self:
                w.setParent(None)
        except (RuntimeError, SystemError):
            pass

    def raise_surface(self, widget):
        if self._restacking:
            return
        self.renderer.raise_surface(widget)
        self._restack()

    def lower_surface(self, widget):
        if self._restacking:
            return
        self.renderer.lower_surface(widget)
        self._restack()

    def _never_materialize(self, w):
        return _prop(w, PROP_NEVER_MAT) is True

    def _hover_materialize(self, w):
        return _prop(w, PROP_HOVER_MAT) is True

    def materialize(self, w, by_hover=False):
        if not _alive(w):
            return
        if self._never_materialize(w):
            return

        if w is self._materialized:
            self._restack()
            return

        prev = self._materialized
        if prev is not None and _alive(prev):
            try:
                prev.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                prev.clearFocus()
            except (RuntimeError, SystemError):
                pass

        self._materialized = w
        self._materialized_by_hover = bool(by_hover)

        reg = self.renderer._reg_by_widget.get(w)
        if reg is not None:
            self.renderer._apply_dont_show(reg, False)

        self.renderer.raise_surface(w)

        try:
            w.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        except (RuntimeError, SystemError):
            return

        self.renderer._materialized_widget = w
        self._restack()

        give = getattr(w, "give_focus", None)
        if callable(give):
            try:
                give()
            except Exception:
                pass
        else:
            try:
                w.setFocus(Qt.FocusReason.MouseFocusReason)
            except (RuntimeError, SystemError):
                pass

        self.renderer._request_frame()

    def dematerialize(self):
        if self._materialized is None:
            return
        w = self._materialized
        self._materialized = None
        self._materialized_by_hover = False
        self.renderer._materialized_widget = None
        if _alive(w):
            try:
                w.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            except (RuntimeError, SystemError):
                pass
            reg = self.renderer._reg_by_widget.get(w)
            if reg is not None:
                self.renderer._apply_dont_show(reg, True)
            try:
                self.renderer.force_refresh(w)
            except (RuntimeError, SystemError):
                pass
        self._restack()
        self.renderer._request_frame()

    def _clear_focus(self):
        fw = QApplication.focusWidget()
        if fw is not None:
            try:
                fw.clearFocus()
            except (RuntimeError, SystemError):
                pass
        try:
            self.clearFocus()
        except (RuntimeError, SystemError):
            pass

    def _restack(self):
        if self._restacking:
            return
        self._restacking = True
        try:
            for r in self.renderer._regs:
                w = r.widget
                if w is self._materialized:
                    continue
                if not _alive(w):
                    continue
                if w.parentWidget() is self and w.isVisible():
                    try:
                        _q_raise(w)
                    except (RuntimeError, SystemError):
                        pass

            if _alive(self.renderer):
                try:
                    _q_raise(self.renderer)
                except (RuntimeError, SystemError):
                    pass

            m = self._materialized
            if m is not None and _alive(m):
                try:
                    if not m.isVisible():
                        _q_show(m)
                    _q_raise(m)
                except (RuntimeError, SystemError):
                    pass
        finally:
            self._restacking = False

    def hit(self, pos):
        for r in reversed(self.renderer._regs):
            w = r.widget
            if not _alive(w):
                continue
            if not w.isVisible():
                continue
            if not _paintable(w):
                continue
            rect = QRect(w.x(), w.y(), w.width(), w.height())
            if rect.contains(pos):
                return w
        return None

    def _on_hover(self, pos):
        target = self.hit(pos)
        if target is self._materialized:
            return
        if target is None or self._never_materialize(target):
            if (self._materialized is not None
                    and self._materialized_by_hover):
                self.dematerialize()
            return
        if self._hover_materialize(target):
            self.materialize(target, by_hover=True)
            return
        if (self._materialized is not None
                and self._materialized_by_hover):
            self.dematerialize()

    def _on_click(self, pos):
        target = self.hit(pos)
        if target is None or self._never_materialize(target):
            self.dematerialize()
            self._clear_focus()
            return
        if target is self._materialized:
            self._restack()
            self.renderer._request_frame()
            return
        self.materialize(target, by_hover=False)

    def mouseMoveEvent(self, ev):
        try:
            pos = ev.position().toPoint()
        except (RuntimeError, SystemError, AttributeError):
            return super().mouseMoveEvent(ev)
        self._on_hover(pos)
        super().mouseMoveEvent(ev)

    def mousePressEvent(self, ev):
        try:
            pos = ev.position().toPoint()
        except (RuntimeError, SystemError, AttributeError):
            return super().mousePressEvent(ev)
        self._on_click(pos)
        super().mousePressEvent(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.renderer is not None and _alive(self.renderer):
            self.renderer.setGeometry(0, 0, self.width(), self.height())