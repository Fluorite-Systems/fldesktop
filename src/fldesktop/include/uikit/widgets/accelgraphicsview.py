from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QImage, QKeySequence
from PySide6.QtCore import Qt, Signal, QThread, QSize, QRect
from fldesktop.include.uikit.widgets.base import Widget
import mmap
import os
import logging
import struct
import uuid


HEADER_SIZE = 16
_HDR        = struct.Struct('<IIII')
_EMPTY_HDR  = _HDR.pack(0, 0, 0, 0)
_DIRTY      = 0x1
_HALF       = 0x80000000


def _is_newer(a: int, b: int) -> bool:
    d = (a - b) & 0xFFFFFFFF
    return 0 < d < _HALF


class ImageViewer(QWidget):
    frameReceived = Signal(object)
    sizeChanged = Signal(QSize)
    inputEvent = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self._image_data = None
        self._qimg = None
        self._img_rect = None
        self._width = 640
        self._height = 480

    def set_image(self, data: bytes, width: int, height: int) -> None:
        self._image_data = data
        self._width = width
        self._height = height
        self._qimg = QImage(
            data, width, height, 3 * width, QImage.Format.Format_RGB888
        )
        self._img_rect = None
        self.frameReceived.emit(data)
        self.update()

    def resizeEvent(self, event) -> None:
        self._img_rect = None
        self.sizeChanged.emit(event.size())
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        qimg = self._qimg
        if qimg is None or qimg.isNull():
            p.fillRect(self.rect(), Qt.GlobalColor.darkGray)
            p.end()
            return

        if self._img_rect is None:
            iw, ih = qimg.width(), qimg.height()
            dw, dh = self.width(), self.height()
            if iw <= 0 or ih <= 0 or dw <= 0 or dh <= 0:
                p.fillRect(self.rect(), Qt.GlobalColor.black)
                p.end()
                return
            if iw * dh > ih * dw:
                sw = dw
                sh = max(1, ih * dw // iw)
            else:
                sw = max(1, iw * dh // ih)
                sh = dh
            self._img_rect = QRect((dw - sw) // 2, (dh - sh) // 2, sw, sh)

        p.fillRect(self.rect(), Qt.GlobalColor.black)
        p.drawImage(self._img_rect, qimg)
        p.end()

    def _key_text(self, event) -> str:
        text = event.text()
        if text and text.isprintable():
            return text
        return QKeySequence(event.keyCombination()).toString(
            QKeySequence.SequenceFormat.PortableText
        )

    def keyPressEvent(self, event) -> None:
        self.inputEvent.emit({
            "event_type": "key_press",
            "code": event.key(),
            "key": self._key_text(event),
        })

    def keyReleaseEvent(self, event) -> None:
        self.inputEvent.emit({
            "event_type": "key_release",
            "code": event.key(),
            "key": self._key_text(event),
        })

    def mousePressEvent(self, event) -> None:
        pt = event.position().toPoint()
        self.inputEvent.emit({
            "event_type": "mouse_press",
            "button": event.button().value,
            "x": pt.x(), "y": pt.y(),
        })

    def mouseReleaseEvent(self, event) -> None:
        pt = event.position().toPoint()
        self.inputEvent.emit({
            "event_type": "mouse_release",
            "button": event.button().value,
            "x": pt.x(), "y": pt.y(),
        })

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        self.inputEvent.emit({
            "event_type": "mouse_move",
            "x": int(pos.x()), "y": int(pos.y()),
        })

    def wheelEvent(self, event) -> None:
        self.inputEvent.emit({
            "event_type": "mouse_wheel",
            "delta": -int(event.angleDelta().y()),
        })


class SharedMemoryReceiver:
    def __init__(self, buffer_size: int) -> None:
        self.buffer_size = buffer_size
        self.header_size = HEADER_SIZE
        self.shm_path = f"/dev/shm/{uuid.uuid4()}"
        self.mmap = None
        self.fd = None
        self.connected = False
        self._last_seq = 0

    def connect(self) -> bool:
        self.close(unlink=False)
        fd = None
        mm = None
        try:
            fd = os.open(self.shm_path, os.O_RDWR | os.O_CREAT, 0o666)
            try:
                os.ftruncate(fd, self.buffer_size * 2)
                size = os.fstat(fd).st_size
                if size < self.buffer_size * 2:
                    os.close(fd)
                    return False
                mm = mmap.mmap(
                    fd, size,
                    mmap.MAP_SHARED,
                    mmap.PROT_READ | mmap.PROT_WRITE,
                )
            except Exception:
                try:
                    os.close(fd)
                except Exception:
                    pass
                return False

            mm[0:HEADER_SIZE] = _EMPTY_HDR
            mm[self.buffer_size:self.buffer_size + HEADER_SIZE] = _EMPTY_HDR

            self.fd = fd
            self.mmap = mm
            self._last_seq = 0
            self.connected = True
            logging.debug("Receiver SHM: %s", self.shm_path)
            return True
        except Exception:
            if mm is not None:
                try: mm.close()
                except Exception: pass
            if fd is not None:
                try: os.close(fd)
                except Exception: pass
            return False

    def receive(self):
        mm = self.mmap
        if not self.connected or mm is None:
            return None
        bs = self.buffer_size

        try:
            best_diff = 0
            best_idx = -1
            best_seq = best_w = best_h = 0

            for i in (0, 1):
                off = i * bs
                seq, w, h, flags = _HDR.unpack(mm[off:off + HEADER_SIZE])
                if flags & _DIRTY:
                    continue
                if w == 0 or h == 0:
                    continue
                size = w * h * 3
                if HEADER_SIZE + size > bs:
                    continue
                if not _is_newer(seq, self._last_seq):
                    continue
                diff = (seq - self._last_seq) & 0xFFFFFFFF
                if diff > best_diff:
                    best_diff = diff
                    best_idx = i
                    best_seq, best_w, best_h = seq, w, h

            if best_idx < 0:
                return None

            off = best_idx * bs
            size = best_w * best_h * 3
            data = mm[off + HEADER_SIZE: off + HEADER_SIZE + size]

            seq2, w2, h2, flags2 = _HDR.unpack(mm[off:off + HEADER_SIZE])
            if (flags2 & _DIRTY) or seq2 != best_seq \
               or w2 != best_w or h2 != best_h:
                return None

            self._last_seq = best_seq
            return data, best_w, best_h
        except Exception:
            return None

    def close(self, unlink: bool = False) -> None:
        if self.mmap is not None:
            try: self.mmap.close()
            except Exception: pass
            self.mmap = None
        if self.fd is not None:
            try: os.close(self.fd)
            except Exception: pass
            self.fd = None
        if unlink:
            try: os.unlink(self.shm_path)
            except OSError: pass
        self.connected = False


class ReceiverThread(QThread):
    frameReceived = Signal(bytes, int, int)
    errorOccurred = Signal(str)

    def __init__(self, buffer_size: int) -> None:
        super().__init__()
        self.rx = SharedMemoryReceiver(buffer_size)
        self.running = False
        self._idle_sleep_us = 15000
        self._busy_sleep_us = 2000

    def run(self) -> None:
        self.setPriority(QThread.Priority.InheritPriority)

        if not self.rx.connect():
            self.errorOccurred.emit("Connect fail")
            self.rx.close(unlink=True)
            return

        self.running = True
        while self.running:
            try:
                result = self.rx.receive()
                if result is not None:
                    self.frameReceived.emit(*result)
                    QThread.usleep(self._busy_sleep_us)
                else:
                    QThread.usleep(self._idle_sleep_us)
            except Exception as e:
                self.rx.close(unlink=False)
                if not self.rx.connect():
                    self.errorOccurred.emit(f"Reconnect fail: {e}")
                    self.running = False
                    break

        self.rx.close(unlink=True)

    def stop(self) -> None:
        self.running = False
        self.quit()
        self.wait()


class Receiver:
    def __init__(self, buffer_size: int) -> None:
        self.thread = ReceiverThread(buffer_size)
        self.thread.errorOccurred.connect(self._on_error)
        self._running = False

    @property
    def shm_path(self) -> str:
        return self.thread.rx.shm_path

    def _on_error(self, text: str) -> None:
        logging.warning("Receiver error: %s", text)

    def start(self) -> None:
        if not self._running:
            self.thread.start()
            self._running = True

    def stop(self) -> None:
        if self._running:
            self.thread.stop()
            self._running = False


class AccelGraphicsView(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = ImageViewer()

        super().__init__(comm, name, attrs) 

        self.type = "accelgraphicsview"
        self.rx = None        

        self.callables = {
            "start": self.start,
            "stop": self.stop
        }

        self._setup()

        self.qwidget.sizeChanged.connect(self._handle_resize)
        self.qwidget.inputEvent.connect(self._handle_input)

    def _cleanup(self):
        self.stop()

    def _handle_resize(self, size: QSize):
        
        self.event(
            type="accelgraphicsview_view_size_changed",
            width=size.width(),
            height=size.height()
        )

    def _handle_input(self, event: dict):

        self.event(
            type="accelgraphicsview_input",
            **event
        )

    def start(self):
        if self.rx:
            self.rx.stop()

        ssize = self.qwidget.screen().size()
        bs = ssize.width() * ssize.height() * 3

        self.rx = Receiver(bs)
        self.rx.thread.frameReceived.connect(self.qwidget.set_image)
        self.rx.start()

        return {
            "shm_path": self.rx.thread.rx.shm_path,
            "buffer_size": bs
        }

    def stop(self):
        if self.rx:
            self.rx.stop()
            self.rx = None

