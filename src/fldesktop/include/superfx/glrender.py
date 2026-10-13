import ctypes
import time
from dataclasses import dataclass

import numpy as np

from PySide6.QtCore import QEvent, QPoint, QRect, QTimer, Qt
from PySide6.QtGui import QImage, QOpenGLContext, QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication, QWidget

from OpenGL.GL import *
from fldesktop.include.superfx.shaders import *


PROP_LAYER = "compositor.layer"
PROP_LAYER_LOCKED = "compositor.layer_locked"
PROP_ENABLE_GLOW = "compositor.enable_glow"
PROP_TINT_SCALE = "compositor.tint_amount_scale"
PROP_TINT_COLOR = "compositor.tint_color"
PROP_HOVER_MAT = "compositor.materialize_on_hover"
PROP_NEVER_MAT = "compositor.never_materialize"

DEFAULT_LAYER = 1.0

GL_CTX_VERSION = (4, 4)
GL_SWAP_INTERVAL = 1
BLUR_LEVELS = 4
SHOW_FPS = True
FPS_REFRESH_S = 1.0
FRAME_INTERVAL_MS = 16

SAFETY_REFRESH_MS = 250.0

MAX_TEX_DIM = 16384


@dataclass
class GlassConfig:
    tint: tuple = (0.1, 0.1, 0.1)
    tint_amount: float = 0.4
    blur_strength: float = 0.5

    shadow_offset: tuple = (0.004, 0.004)
    shadow_spread: float = 0.014
    shadow_alpha: float = 0.55

    wave_strength: float = 0.15
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


class _Reg:
    __slots__ = ("widget", "z", "glass", "layer", "locked",
                 "tex", "img", "tex_wh", "dirty", "last_refresh")

    def __init__(self, widget, z, glass, layer, locked):
        self.widget = widget
        self.z = float(z)
        self.glass = bool(glass)
        self.layer = float(layer)
        self.locked = bool(locked)
        self.tex = None
        self.img = None
        self.tex_wh = None
        self.dirty = True
        self.last_refresh = 0.0

    @property
    def geom(self):
        w = self.widget
        return (w.x(), w.y(), w.width(), w.height())


class GLRender(QOpenGLWidget):
    def __init__(self, parent, config=None):
        super().__init__(parent)
        if config is None:
            config = GlassConfig()
        self.config = config

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.NoPartialUpdate)

        self._t0 = time.perf_counter()
        self._regs = []
        self._reg_by_widget = {}
        self._materialized_widget = None

        self._progs = {}
        self._uni = {}
        self._vao = 0
        self._vbo = 0

        self._scene_fbo = None
        self._scene_tex = None
        self._blur_src_fbo = None
        self._blur_src_tex = None
        self._scene_size = (0, 0)

        self._blur_down_fbos = []
        self._blur_down_texs = []
        self._blur_down_sizes = []
        self._blur_up_fbos = []
        self._blur_up_texs = []
        self._blur_up_sizes = []

        self._win_fbo = None
        self._win_tex = None
        self._win_size = (0, 0)

        self._wallpaper_image = None
        self._wallpaper_tex = None

        self._gl_ctx = None
        self._shutting_down = False
        self._max_tex_dim = MAX_TEX_DIM

        self._frames = 0
        self._fps_t = time.perf_counter()
        self._fps = 0.0

        self._tick = QTimer(self)
        self._tick.setTimerType(Qt.TimerType.PreciseTimer)
        self._tick.setInterval(FRAME_INTERVAL_MS)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def _on_tick(self):
        if _app_closing() or self._shutting_down:
            try:
                self._tick.stop()
            except (RuntimeError, SystemError):
                pass
            return
        try:
            self.update()
        except (RuntimeError, SystemError):
            pass

    def _tex_ok(self, w, h):
        return 0 < w <= self._max_tex_dim and 0 < h <= self._max_tex_dim

    def _ensure_context(self):
        try:
            ctx = QOpenGLContext.currentContext()
        except (RuntimeError, SystemError):
            return False
        if ctx is None:
            return False
        same = False
        try:
            same = (ctx == self._gl_ctx)
        except Exception:
            same = False
        if not same:
            self._forget_gl_resources()
            self._rebuild_gl()
            self._gl_ctx = ctx
        return True

    def _forget_gl_resources(self):
        self._progs = {}
        self._uni = {}
        self._vao = 0
        self._vbo = 0

        self._scene_fbo = None
        self._scene_tex = None
        self._blur_src_fbo = None
        self._blur_src_tex = None
        self._scene_size = (0, 0)
        self._blur_down_fbos = []
        self._blur_down_texs = []
        self._blur_down_sizes = []
        self._blur_up_fbos = []
        self._blur_up_texs = []
        self._blur_up_sizes = []

        self._win_fbo = None
        self._win_tex = None
        self._win_size = (0, 0)

        self._wallpaper_tex = None
        for r in self._regs:
            r.tex = None
            r.tex_wh = None
            r.dirty = True

    def _rebuild_gl(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)
        glPixelStorei(GL_UNPACK_SKIP_ROWS, 0)
        glPixelStorei(GL_UNPACK_SKIP_PIXELS, 0)

        try:
            m = int(glGetInteger(GL_MAX_TEXTURE_SIZE))
            if m > 0:
                self._max_tex_dim = min(MAX_TEX_DIM, m)
        except Exception:
            pass

        self._progs = {
            "kawase_down": self._link(
                VERT_SRC, FRAG_KAWASE_DOWN_SRC, "kawase_down"),
            "kawase_up": self._link(
                VERT_SRC, FRAG_KAWASE_UP_SRC, "kawase_up"),
            "copy": self._link(VERT_SRC, FRAG_COPY_SRC, "copy"),
            "window": self._link(VERT_SRC, FRAG_WINDOW_SRC, "window"),
        }
        self._uni = {k: self._collect(p) for k, p in self._progs.items()}
        self._create_quad()

    def set_wallpaper(self, image):
        self._drop_wallpaper_tex()
        self._wallpaper_image = image
        try:
            self.update()
        except (RuntimeError, SystemError):
            pass

    def register(self, widget, z=1.0, glass=True,
                 layer=None, locked=None):
        for r in self._regs:
            if r.widget is widget:
                return r

        if layer is None:
            layer = _coerce_layer(_prop(widget, PROP_LAYER))
        else:
            layer = _coerce_layer(layer)

        if locked is None:
            locked = bool(_prop(widget, PROP_LAYER_LOCKED))
        else:
            locked = bool(locked)

        r = _Reg(widget, z, glass, layer, locked)
        self._regs.append(r)
        self._regs.sort(key=lambda x: (x.layer, x.z))
        self._reg_by_widget[widget] = r
        try:
            self.update()
        except (RuntimeError, SystemError):
            pass
        return r

    def unregister(self, widget):
        for r in self._regs:
            if r.widget is widget:
                self._regs.remove(r)
                self._reg_by_widget.pop(widget, None)

                tex = r.tex
                r.tex = None
                r.img = None
                r.tex_wh = None

                if (tex is not None
                        and self.isValid()
                        and not _app_closing()
                        and not self._shutting_down):
                    try:
                        self.makeCurrent()
                        glActiveTexture(GL_TEXTURE0)
                        glDeleteTextures(1, [tex])
                        self.doneCurrent()
                    except (RuntimeError, SystemError, GLError):
                        pass
                try:
                    self.update()
                except (RuntimeError, SystemError):
                    pass
                return True
        return False

    def raise_surface(self, widget):
        r = self._reg_by_widget.get(widget)
        if r is None or r.locked:
            return
        peers = [x for x in self._regs
                 if x is not r and x.layer == r.layer]
        if not peers:
            return
        top = max(x.z for x in peers)
        if r.z >= top:
            return
        r.z = top + 1.0
        self._regs.sort(key=lambda x: (x.layer, x.z))
        try:
            self.update()
        except (RuntimeError, SystemError):
            pass

    def lower_surface(self, widget):
        r = self._reg_by_widget.get(widget)
        if r is None or r.locked:
            return
        peers = [x for x in self._regs
                 if x is not r and x.layer == r.layer]
        if not peers:
            return
        r.z = min(x.z for x in peers) - 1.0
        self._regs.sort(key=lambda x: (x.layer, x.z))
        try:
            self.update()
        except (RuntimeError, SystemError):
            pass

    def invalidate(self, widget=None):
        if widget is None:
            for r in self._regs:
                r.dirty = True
        else:
            r = self._reg_by_widget.get(widget)
            if r is not None:
                r.dirty = True
        try:
            self.update()
        except (RuntimeError, SystemError):
            pass

    def force_refresh(self, widget):
        r = self._reg_by_widget.get(widget)
        if r is not None:
            r.dirty = True

    def eventFilter(self, obj, ev):
        if not isinstance(obj, QWidget):
            return False
        if _app_closing() or self._shutting_down:
            return False
        et = ev.type()
        if et in (QEvent.Type.UpdateRequest,
                  QEvent.Type.Move,
                  QEvent.Type.Resize,
                  QEvent.Type.Show):
            r = self._reg_of(obj)
            if r is not None:
                if et in (QEvent.Type.UpdateRequest,
                          QEvent.Type.Resize,
                          QEvent.Type.Show):
                    r.dirty = True
                try:
                    self.update()
                except (RuntimeError, SystemError):
                    pass
            return False
        return False

    def _reg_of(self, w):
        while w is not None:
            r = self._reg_by_widget.get(w)
            if r is not None:
                return r
            try:
                w = w.parentWidget()
            except (RuntimeError, SystemError):
                return None
        return None

    def initializeGL(self):
        print("GL:", glGetString(GL_VERSION).decode(),
              "|", glGetString(GL_RENDERER).decode())
        self._rebuild_gl()
        try:
            self._gl_ctx = QOpenGLContext.currentContext()
        except (RuntimeError, SystemError):
            self._gl_ctx = None

    def resizeGL(self, w, h):
        if w <= 0 or h <= 0:
            return
        if not self._ensure_context():
            return
        self._setup_fbos()

    def closeEvent(self, ev):
        self._shutting_down = True

        try:
            self._tick.stop()
        except (RuntimeError, SystemError):
            pass

        app = QApplication.instance()
        if app is not None:
            try:
                app.removeEventFilter(self)
            except (RuntimeError, SystemError):
                pass

        try:
            if self.isValid():
                self.makeCurrent()
                try:
                    self._destroy_fbos()
                except Exception:
                    pass
                try:
                    self._drop_wallpaper_tex()
                except Exception:
                    pass
                for r in self._regs:
                    tex = r.tex
                    r.tex = None
                    r.img = None
                    r.tex_wh = None
                    if tex is not None:
                        try:
                            glDeleteTextures(1, [tex])
                        except Exception:
                            pass
                for p in self._progs.values():
                    try:
                        glDeleteProgram(p)
                    except Exception:
                        pass
                self._progs.clear()
                self._uni.clear()
                try:
                    if self._vbo:
                        glDeleteBuffers(1, [self._vbo])
                    self._vbo = 0
                except Exception:
                    pass
                try:
                    if self._vao:
                        glDeleteVertexArrays(1, [self._vao])
                    self._vao = 0
                except Exception:
                    pass
                self.doneCurrent()
        except Exception:
            pass

        for r in self._regs:
            r.widget = None
        self._regs.clear()
        self._reg_by_widget.clear()
        self._materialized_widget = None
        self._wallpaper_image = None

        super().closeEvent(ev)

    def _compile(self, src, kind):
        sh = glCreateShader(kind)
        glShaderSource(sh, src)
        glCompileShader(sh)
        if not glGetShaderiv(sh, GL_COMPILE_STATUS):
            raise RuntimeError(glGetShaderInfoLog(sh).decode())
        return sh

    def _link(self, vs, fs, name):
        v = self._compile(vs, GL_VERTEX_SHADER)
        f = self._compile(fs, GL_FRAGMENT_SHADER)
        p = glCreateProgram()
        glAttachShader(p, v)
        glAttachShader(p, f)
        glLinkProgram(p)
        if not glGetProgramiv(p, GL_LINK_STATUS):
            raise RuntimeError(
                f"[{name}] {glGetProgramInfoLog(p).decode()}")
        glDeleteShader(v)
        glDeleteShader(f)
        return p

    def _collect(self, program):
        out = {}
        for i in range(glGetProgramiv(program, GL_ACTIVE_UNIFORMS)):
            name, _, _ = glGetActiveUniform(program, i)
            loc = glGetUniformLocation(program, name)
            if loc < 0:
                continue
            n = name.decode() if isinstance(name, bytes) else name
            if n.endswith("[0]"):
                n = n[:-3]
            out[n] = loc
        return out

    def _set(self, prog, name, *v):
        loc = self._uni.get(prog, {}).get(name, -1)
        if loc < 0:
            return
        if len(v) == 1:
            glUniform1f(loc, v[0])
        elif len(v) == 2:
            glUniform2f(loc, v[0], v[1])
        elif len(v) == 3:
            glUniform3f(loc, v[0], v[1], v[2])
        elif len(v) == 4:
            glUniform4f(loc, v[0], v[1], v[2], v[3])

    def _seti(self, prog, name, value):
        loc = self._uni.get(prog, {}).get(name, -1)
        if loc >= 0:
            glUniform1i(loc, value)

    def _create_quad(self):
        verts = np.array(
            [-1, -1, 0, 0, 1, -1, 1, 0, -1, 1, 0, 1, 1, 1, 1, 1],
            dtype=np.float32)
        self._vao = glGenVertexArrays(1)
        glBindVertexArray(self._vao)
        self._vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16,
                              ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16,
                              ctypes.c_void_p(8))
        glBindVertexArray(0)

    def _make_tex(self, w, h):
        if not self._tex_ok(w, h):
            return 0
        glActiveTexture(GL_TEXTURE0)
        tex = glGenTextures(1)
        if not tex:
            return 0
        glBindTexture(GL_TEXTURE_2D, tex)
        try:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, None)
        except GLError as e:
            print(f"[GLRender] glTexImage2D failed ({w}x{h}): {e}")
            try:
                glDeleteTextures(1, [tex])
            except Exception:
                pass
            return 0
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return int(tex)

    def _make_fbo(self, w, h):
        tex = self._make_tex(w, h)
        if not tex:
            return None, None
        fbo = glGenFramebuffers(1)
        if not fbo:
            glActiveTexture(GL_TEXTURE0)
            glDeleteTextures(1, [tex])
            return None, None
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                               GL_TEXTURE_2D, tex, 0)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        if status != GL_FRAMEBUFFER_COMPLETE:
            print(f"[GLRender] FBO incomplete: status=0x{status:x} "
                  f"size={w}x{h}")
            glDeleteFramebuffers(1, [fbo])
            glActiveTexture(GL_TEXTURE0)
            glDeleteTextures(1, [tex])
            return None, None
        return fbo, tex

    def _setup_fbos(self):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0 or self._scene_size == (w, h):
            return
        self._destroy_fbos()

        scene_fbo, scene_tex = self._make_fbo(w, h)
        blur_fbo, blur_tex = self._make_fbo(w, h)
        self._scene_fbo = scene_fbo
        self._scene_tex = scene_tex
        self._blur_src_fbo = blur_fbo
        self._blur_src_tex = blur_tex

        if scene_fbo is None or blur_fbo is None:
            print("[GLRender] scene FBO creation failed; will retry")
            self._destroy_fbos()
            return

        for i in range(BLUR_LEVELS):
            bw = max(1, w >> (i + 1))
            bh = max(1, h >> (i + 1))
            f, t = self._make_fbo(bw, bh)
            self._blur_down_fbos.append(f)
            self._blur_down_texs.append(t)
            self._blur_down_sizes.append((bw, bh))
        for i in range(BLUR_LEVELS):
            lvl = BLUR_LEVELS - i - 1
            bw = max(1, w >> lvl)
            bh = max(1, h >> lvl)
            f, t = self._make_fbo(bw, bh)
            self._blur_up_fbos.append(f)
            self._blur_up_texs.append(t)
            self._blur_up_sizes.append((bw, bh))

        self._scene_size = (w, h)
        for r in self._regs:
            r.tex_wh = None
            r.dirty = True

    def _destroy_fbos(self):
        glActiveTexture(GL_TEXTURE0)

        pairs = [(self._scene_fbo, self._scene_tex),
                 (self._blur_src_fbo, self._blur_src_tex)]
        for f, t in pairs:
            if f:
                glDeleteFramebuffers(1, [f])
            if t:
                glDeleteTextures(1, [t])
        self._scene_fbo = self._scene_tex = None
        self._blur_src_fbo = self._blur_src_tex = None

        for f, t in zip(self._blur_down_fbos, self._blur_down_texs):
            if f:
                glDeleteFramebuffers(1, [f])
            if t:
                glDeleteTextures(1, [t])
        self._blur_down_fbos.clear()
        self._blur_down_texs.clear()
        self._blur_down_sizes.clear()

        for f, t in zip(self._blur_up_fbos, self._blur_up_texs):
            if f:
                glDeleteFramebuffers(1, [f])
            if t:
                glDeleteTextures(1, [t])
        self._blur_up_fbos.clear()
        self._blur_up_texs.clear()
        self._blur_up_sizes.clear()

        if self._win_fbo:
            glDeleteFramebuffers(1, [self._win_fbo])
            self._win_fbo = None
        if self._win_tex:
            glDeleteTextures(1, [self._win_tex])
            self._win_tex = None
        self._win_size = (0, 0)
        self._scene_size = (0, 0)

    def _drop_wallpaper_tex(self):
        tex = self._wallpaper_tex
        self._wallpaper_tex = None
        if (tex is not None
                and self.isValid()
                and not _app_closing()
                and not self._shutting_down):
            try:
                self.makeCurrent()
                glActiveTexture(GL_TEXTURE0)
                glDeleteTextures(1, [tex])
                self.doneCurrent()
            except (RuntimeError, SystemError, GLError):
                pass

    def _ensure_win_fbo(self, w, h):
        if (self._win_fbo is not None
                and self._win_size[0] >= w and self._win_size[1] >= h):
            return
        nw = max(w, self._win_size[0])
        nh = max(h, self._win_size[1])
        if not self._tex_ok(nw, nh):
            return
        if self._win_fbo is not None:
            glDeleteFramebuffers(1, [self._win_fbo])
            glDeleteTextures(1, [self._win_tex])
            self._win_fbo = None
            self._win_tex = None
            self._win_size = (0, 0)
        fbo, tex = self._make_fbo(nw, nh)
        self._win_fbo = fbo
        self._win_tex = tex
        if fbo is None:
            self._win_size = (0, 0)
        else:
            self._win_size = (nw, nh)

    def _upload(self, img):
        img = img.convertToFormat(
            QImage.Format.Format_RGBA8888_Premultiplied)
        w, h = img.width(), img.height()
        if not self._tex_ok(w, h):
            return 0
        row = img.bytesPerLine()
        arr = np.frombuffer(img.constBits(), dtype=np.uint8)
        arr = arr.reshape(h, row)[:, :w * 4]
        arr = arr.reshape(h, w, 4)[::-1].copy()

        glActiveTexture(GL_TEXTURE0)
        tex = self._make_tex(w, h)
        if not tex:
            return 0
        glBindTexture(GL_TEXTURE_2D, tex)
        try:
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h,
                            GL_RGBA, GL_UNSIGNED_BYTE, arr.tobytes())
        except GLError as e:
            print(f"[GLRender] wallpaper upload failed: {e}")
            try:
                glDeleteTextures(1, [tex])
            except Exception:
                pass
            return 0
        return tex

    def _refresh_surface_tex(self, r):
        w = r.widget
        if not _alive(w):
            return
        ww, wh = w.width(), w.height()
        if not self._tex_ok(ww, wh):
            return

        fmt = QImage.Format.Format_RGBA8888_Premultiplied
        if r.img is None or r.img.width() != ww or r.img.height() != wh:
            r.img = QImage(ww, wh, fmt)
        r.img.fill(0)

        try:
            w.render(r.img)
        except (RuntimeError, SystemError):
            return

        row = r.img.bytesPerLine()
        arr = np.frombuffer(r.img.constBits(), dtype=np.uint8)
        arr = arr.reshape(wh, row)[:, :ww * 4]
        arr = arr.reshape(wh, ww, 4)[::-1].copy()

        if (r.tex is None
                or r.tex_wh != (ww, wh)):
            old = r.tex
            r.tex = None
            r.tex_wh = None
            if old is not None:
                try:
                    glActiveTexture(GL_TEXTURE0)
                    glDeleteTextures(1, [old])
                except GLError:
                    pass
            r.tex = self._make_tex(ww, wh)
            if not r.tex:
                return
            r.tex_wh = (ww, wh)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, r.tex)
        try:
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, ww, wh,
                            GL_RGBA, GL_UNSIGNED_BYTE, arr.tobytes())
        except GLError as e:
            print(f"[GLRender] surface upload failed ({ww}x{wh}): {e}; "
                  "recreating texture")
            old = r.tex
            r.tex = None
            r.tex_wh = None
            if old is not None:
                try:
                    glDeleteTextures(1, [old])
                except GLError:
                    pass
            r.tex = self._make_tex(ww, wh)
            if not r.tex:
                return
            r.tex_wh = (ww, wh)
            glBindTexture(GL_TEXTURE_2D, r.tex)
            try:
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, ww, wh,
                                GL_RGBA, GL_UNSIGNED_BYTE, arr.tobytes())
            except GLError:
                pass

    def _draw_quad(self):
        glBindVertexArray(self._vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)

    def _kawase(self, prog, src, dst_fbo, dst_size, src_size, scale):
        if not dst_fbo or not src:
            return False
        pid = self._progs.get(prog)
        if not pid:
            return False
        glBindFramebuffer(GL_FRAMEBUFFER, dst_fbo)
        glViewport(0, 0, *dst_size)
        glUseProgram(pid)
        glActiveTexture(GL_TEXTURE0)
        self._seti(prog, "uTexture", 0)
        self._set(prog, "uSrcTexelSize",
                  1.0 / max(1, src_size[0]),
                  1.0 / max(1, src_size[1]))
        self._set(prog, "uBlurScale", scale)
        glBindTexture(GL_TEXTURE_2D, src)
        self._draw_quad()
        return True

    def _blur_levels(self):
        s = float(self.config.blur_strength)
        if s <= 0.0:
            return 0
        if s >= 1.0:
            return BLUR_LEVELS
        return max(1, int(round(s * BLUR_LEVELS)))

    def _blur_scale(self):
        s = float(self.config.blur_strength)
        if s <= 0.0:
            return 0.0
        return max(1.0, s)

    def _blur_texture(self, src_tex):
        if not src_tex:
            return 0
        scale = self._blur_scale()
        levels = self._blur_levels()
        if scale <= 0.0 or levels <= 0:
            return src_tex

        W, H = self._scene_size
        cur = src_tex
        cur_size = (W, H)

        for i in range(levels):
            ds = self._blur_down_sizes[i]
            self._kawase("kawase_down", cur,
                         self._blur_down_fbos[i], ds, cur_size, scale)
            cur = self._blur_down_texs[i]
            cur_size = ds

        base = BLUR_LEVELS - levels
        for i in range(levels):
            j = base + i
            ds = self._blur_up_sizes[j]
            self._kawase("kawase_up", cur,
                         self._blur_up_fbos[j], ds, cur_size, scale)
            cur = self._blur_up_texs[j]
            cur_size = ds

        return cur

    def _enable_glow(self, w):
        v = _prop(w, PROP_ENABLE_GLOW)
        return True if v is None else bool(v)

    def _tint_scale(self, w):
        v = _prop(w, PROP_TINT_SCALE)
        if v is None:
            return 1.0
        try:
            return float(v)
        except (TypeError, ValueError):
            return 1.0

    def _tint_color(self, w):
        v = _prop(w, PROP_TINT_COLOR)
        if v is None:
            return (1.0, 1.0, 1.0)
        try:
            if len(v) == 3:
                return (float(v[0]), float(v[1]), float(v[2]))
        except (TypeError, ValueError, IndexError):
            pass
        return (1.0, 1.0, 1.0)

    def _draw_window(self, r, blurred_tex, W, H, pad_px, draw_surface):
        pid = self._progs.get("window")
        if not pid:
            return
        x, y, ww, wh = r.geom
        w_pad = ww + 2 * pad_px
        h_pad = wh + 2 * pad_px
        if not self._tex_ok(w_pad, h_pad):
            return
        self._ensure_win_fbo(w_pad, h_pad)
        if not self._win_fbo:
            return
        glBindFramebuffer(GL_FRAMEBUFFER, self._win_fbo)
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            if self._win_fbo is not None:
                glDeleteFramebuffers(1, [self._win_fbo])
                glDeleteTextures(1, [self._win_tex])
                self._win_fbo = None
                self._win_tex = None
                self._win_size = (0, 0)
            return
        glViewport(0, 0, w_pad, h_pad)
        glUseProgram(pid)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._scene_tex)
        self._seti("window", "uScene", 0)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, blurred_tex or 0)
        self._seti("window", "uBlurred", 1)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, r.tex or 0)
        self._seti("window", "uSurface", 2)

        cfg = self.config
        ref = float(min(W, H))
        self._set("window", "uResolution", float(W), float(H))
        self._set("window", "uRectMin", x / W, y / H)
        self._set("window", "uRectSize", ww / W, wh / H)
        self._set("window", "uPadUV", pad_px / W, pad_px / H)
        self._set("window", "uShadowOffsetPx",
                  cfg.shadow_offset[0] * ref,
                  cfg.shadow_offset[1] * ref)
        self._set("window", "uShadowSpreadPx", cfg.shadow_spread * ref)
        self._set("window", "uShadowAlpha", cfg.shadow_alpha)
        self._set("window", "uTint", *cfg.tint)
        self._set("window", "uTintColor", *self._tint_color(r.widget))
        self._set("window", "uTintAmount",
                  cfg.tint_amount * self._tint_scale(r.widget))
        self._set("window", "uEnableGlow",
                  1.0 if self._enable_glow(r.widget) else 0.0)
        self._set("window", "uWaveStrength", cfg.wave_strength)
        self._set("window", "uWaveScale", cfg.wave_scale)
        self._set("window", "uWaveAngle", cfg.wave_angle)
        self._set("window", "uTime", time.perf_counter() - self._t0)
        self._set("window", "uGlass", 1.0 if r.glass else 0.0)
        self._set("window", "uDrawSurface", 1.0 if draw_surface else 0.0)
        self._set("window", "uChroma", cfg.chroma)
        self._set("window", "uLens", cfg.lens)
        self._set("window", "uNoise", cfg.noise)
        self._set("window", "uRimStrength", cfg.rim_strength)
        self._set("window", "uSparkleStrength", cfg.sparkle_strength)
        self._set("window", "uEdgeOffset", cfg.edge_offset)
        self._set("window", "uEdgeSensitivity", cfg.edge_sensitivity)

        self._draw_quad()

    def _blit_window(self, geom, W, H, pad_px, target_fbo):
        if not target_fbo or not self._win_fbo:
            return
        x, y, ww, wh = geom
        w_pad = ww + 2 * pad_px
        h_pad = wh + 2 * pad_px
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self._win_fbo)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, target_fbo)
        glReadBuffer(GL_COLOR_ATTACHMENT0)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        gl_y = H - (y - pad_px + h_pad)
        sx0, sy0, sx1, sy1 = 0, 0, w_pad, h_pad
        dx0, dy0 = x - pad_px, gl_y
        dx1, dy1 = dx0 + w_pad, dy0 + h_pad
        if dx0 < 0:
            sx0 -= dx0
            dx0 = 0
        if dy0 < 0:
            sy0 -= dy0
            dy0 = 0
        if dx1 > W:
            sx1 -= dx1 - W
            dx1 = W
        if dy1 > H:
            sy1 -= dy1 - H
            dy1 = H
        if sx1 > sx0 and sy1 > sy0:
            glBlitFramebuffer(sx0, sy0, sx1, sy1,
                              dx0, dy0, dx1, dy1,
                              GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _fill_both_with_wallpaper(self, W, H):
        if self._wallpaper_image is not None and not self._wallpaper_tex:
            self._wallpaper_tex = self._upload(self._wallpaper_image)

        pid = self._progs.get("copy")
        for fbo in (self._scene_fbo, self._blur_src_fbo):
            if not fbo:
                continue
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glViewport(0, 0, W, H)
            glDisable(GL_BLEND)
            glClearColor(0.02, 0.02, 0.03, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            if self._wallpaper_tex and pid:
                glUseProgram(pid)
                glActiveTexture(GL_TEXTURE0)
                self._seti("copy", "uTexture", 0)
                glBindTexture(GL_TEXTURE_2D, self._wallpaper_tex)
                self._draw_quad()

    def _present(self, W, H):
        glBindFramebuffer(GL_FRAMEBUFFER, self.defaultFramebufferObject())
        glViewport(0, 0, W, H)
        glDisable(GL_BLEND)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        pid = self._progs.get("copy")
        if not pid:
            return
        glUseProgram(pid)
        glActiveTexture(GL_TEXTURE0)
        self._seti("copy", "uTexture", 0)
        glBindTexture(GL_TEXTURE_2D, self._scene_tex)
        self._draw_quad()

    def paintGL(self):
        if not self._ensure_context():
            return
        W, H = self.width(), self.height()
        if W <= 0 or H <= 0:
            return
        if self._scene_size != (W, H):
            self._setup_fbos()
        if self._scene_fbo is None or self._blur_src_fbo is None:
            return

        self._fill_both_with_wallpaper(W, H)

        blurred_wallpaper = self._blur_texture(self._blur_src_tex)
        blurred = blurred_wallpaper

        pad_px = int(min(W, H) * self.config.shadow_spread * 5.0) + 16
        now = time.perf_counter()

        visible = []
        for r in self._regs:
            w = r.widget
            if not _alive(w):
                continue
            if not w.isVisible():
                continue
            if not _paintable(w):
                continue
            ww, wh = w.width(), w.height()
            if not self._tex_ok(ww, wh):
                continue
            if r.layer == 0.0 and self._wallpaper_image is not None:
                continue
            visible.append(r)

        for r in visible:
            is_mat = (r.widget is self._materialized_widget)
            ww = r.widget.width()
            wh = r.widget.height()

            stale_size = (r.tex is None) or (r.tex_wh != (ww, wh))
            overdue = (now - r.last_refresh) * 1000.0 >= SAFETY_REFRESH_MS

            if stale_size or r.dirty or overdue:
                self._refresh_surface_tex(r)
                r.dirty = False
                r.last_refresh = now

            source_blur = blurred_wallpaper if is_mat else blurred

            if not is_mat:
                self._draw_window(r, source_blur, W, H, pad_px,
                                  draw_surface=True)
                self._blit_window(r.geom, W, H, pad_px, self._scene_fbo)
                self._blit_window(r.geom, W, H, pad_px, self._blur_src_fbo)
            else:
                self._draw_window(r, source_blur, W, H, pad_px,
                                  draw_surface=False)
                self._blit_window(r.geom, W, H, pad_px, self._scene_fbo)

                self._draw_window(r, source_blur, W, H, pad_px,
                                  draw_surface=True)
                self._blit_window(r.geom, W, H, pad_px, self._blur_src_fbo)

            blurred = self._blur_texture(self._blur_src_tex)

        self._present(W, H)

        self._frames += 1
        if now - self._fps_t >= FPS_REFRESH_S:
            self._fps = self._frames / (now - self._fps_t)
            self._frames = 0
            self._fps_t = now
            if SHOW_FPS and self.window():
                base = (getattr(self.window(), "_base_title", None)
                        or self.window().windowTitle())
                self.window()._base_title = base
                self.window().setWindowTitle(
                    f"{base} — {self._fps:.0f} FPS")


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

        self.gl = GLRender(self, config)
        self.gl.setGeometry(0, 0, self.width(), self.height())
        _q_show(self.gl)
        _q_raise(self.gl)

        self._materialized = None
        self._materialized_by_hover = False
        self._restacking = False

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._on_about_to_quit)

    def _on_about_to_quit(self):
        try:
            if _alive(self.gl):
                self.gl.close()
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
        reg = self.gl.register(w, z=z, glass=glass,
                               layer=layer, locked=locked)
        self._restack()
        return reg

    def remove_surface(self, w):
        if w is self._materialized:
            self._materialized = None
            self._materialized_by_hover = False
            self.gl._materialized_widget = None

        self.gl.unregister(w)

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
        self.gl.raise_surface(widget)
        self._restack()

    def lower_surface(self, widget):
        if self._restacking:
            return
        self.gl.lower_surface(widget)
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

        self.gl.raise_surface(w)

        try:
            w.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        except (RuntimeError, SystemError):
            return

        self.gl._materialized_widget = w
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

        try:
            self.gl.update()
        except (RuntimeError, SystemError):
            pass

    def dematerialize(self):
        if self._materialized is None:
            return
        w = self._materialized
        self._materialized = None
        self._materialized_by_hover = False
        self.gl._materialized_widget = None
        if _alive(w):
            try:
                w.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            except (RuntimeError, SystemError):
                pass
            try:
                self.gl.force_refresh(w)
            except (RuntimeError, SystemError):
                pass
        self._restack()
        try:
            self.gl.update()
        except (RuntimeError, SystemError):
            pass

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
            for r in self.gl._regs:
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

            if _alive(self.gl):
                try:
                    _q_raise(self.gl)
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
        for r in reversed(self.gl._regs):
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
            try:
                self.gl.update()
            except (RuntimeError, SystemError):
                pass
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
        if self.gl is not None and _alive(self.gl):
            self.gl.setGeometry(0, 0, self.width(), self.height())


def configure_opengl():
    fmt = QSurfaceFormat()
    fmt.setVersion(*GL_CTX_VERSION)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSwapInterval(GL_SWAP_INTERVAL)
    QSurfaceFormat.setDefaultFormat(fmt)