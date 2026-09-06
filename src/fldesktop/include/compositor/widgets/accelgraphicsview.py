from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QImage, QKeySequence
from PySide6.QtCore import Qt, Signal, QThread, QSize
from fldesktop.include.compositor.widgets.base import Widget
import mmap
import os
import logging
import struct
import uuid


class ImageViewer(QWidget):
    frameReceived = Signal(object)
    sizeChanged = Signal(QSize)
    inputEvent = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._image_data = None
        self._width = 640
        self._height = 480

    def set_image(self, data: bytes, width: int, height: int):
        self._image_data = data
        self._width = width
        self._height = height
        self.frameReceived.emit(data)
        self.update()

    def resizeEvent(self, event):
        self.sizeChanged.emit(event.size())
        super().resizeEvent(event)

    def paintEvent(self, event):
        def draw_blank(self):
            p = QPainter(self)
            p.fillRect(self.rect(), Qt.darkGray)
            p.end()

        if self._image_data is None:
            draw_blank(self)
            return

        bpl = 3 * self._width
        qimg = QImage(self._image_data, self._width, self._height,
                      bpl, QImage.Format_RGB888)
        if qimg.isNull():
            draw_blank(self)
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.fillRect(self.rect(), Qt.black)

        scaled = qimg.scaled(self.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        p.drawImage(x, y, scaled)
        p.end()

    def keyPressEvent(self, event):
        self.inputEvent.emit(
            {
                "event_type": "key_press",
                "code": event.key(),
                "key": QKeySequence(event.keyCombination()).toString(
                            QKeySequence.SequenceFormat.PortableText
                        ) if not event.text().isprintable() \
                        and event.text() != "" else event.text()
            }
        )

    def keyReleaseEvent(self, event):
        self.inputEvent.emit(
            {
                "event_type": "key_release",
                "code": event.key(),
                "key": QKeySequence(event.keyCombination()).toString(
                            QKeySequence.SequenceFormat.PortableText
                        ) if not event.text().isprintable() \
                        and event.text() != "" else event.text()
            }
        )

    def mousePressEvent(self, event):
        self.inputEvent.emit(
            {
                "event_type": "mouse_press",
                "button": event.button().value,
                "x": event.position().toPoint().x(),
                "y": event.position().toPoint().y()
            }
        )

    def mouseReleaseEvent(self, event):
        self.inputEvent.emit(
            {
                "event_type": "mouse_release",
                "button": event.button().value,
                "x": event.position().toPoint().x(),
                "y": event.position().toPoint().y()
            }
        )

    def mouseMoveEvent(self, event):
        self.inputEvent.emit(
            {
                "event_type": "mouse_move",
                "x": int(event.position().x()),
                "y": int(event.position().y())
            }
        )

    def wheelEvent(self, event):
        self.inputEvent.emit(
            {
                "event_type": "mouse_wheel",
                "delta": int(event.angleDelta().y())
            }
        )


class SharedMemoryReceiver:
    def __init__(self, buffer_size: int):
        self.buffer_size = buffer_size
        self.header_size = 8
        self.shm_path = f"/dev/shm/{str(uuid.uuid4())}"
        self.mmap = None
        self.fd = None
        self.connected = False
        self._shm_size = 0

    def connect(self) -> bool:
        self.close()

        logging.debug(f"Creating SHM at {self.shm_path}")

        try:
            self.fd = os.open(self.shm_path, os.O_RDWR | os.O_CREAT, 0o666)
            os.ftruncate(self.fd, self.buffer_size * 2)
            self._shm_size = os.fstat(self.fd).st_size

            if self._shm_size < self.buffer_size * 2:
                os.close(self.fd)
                self.fd = None
                return False

            self.mmap = mmap.mmap(self.fd, self._shm_size,
                                 mmap.MAP_SHARED, mmap.PROT_READ)
            self.connected = True
            return True
        except:
            return False

    def receive(self):
        if not self.connected or self.mmap is None:
            return None

        try:
            try:
                shm_size = self.mmap.size()
            except:
                return None

            for buf_idx in range(2):
                offset = buf_idx * self.buffer_size

                if offset + self.header_size > shm_size:
                    continue

                try:
                    self.mmap.seek(offset)
                    header = self.mmap.read(self.header_size)

                    if len(header) != self.header_size:
                        continue

                    width, height = struct.unpack('II', header)

                    if width <= 0 or height <= 0:
                        continue

                    data_size = width * height * 3

                    if offset + self.header_size + data_size > shm_size:
                        continue

                    data = self.mmap.read(data_size)

                    if len(data) == data_size and any(data):
                        return data, width, height

                except (OSError, ValueError, struct.error):
                    continue

            return None
        except:
            return None

    def close(self): 
        if self.mmap:
            try:
                self.mmap.close()
            except:
                pass
            self.mmap = None
        if self.fd:
            try:
                os.close(self.fd)
            except:
                pass
            self.fd = None
        try:
            os.unlink(self.shm_path)
        except:
            pass
        self.connected = False


class ReceiverThread(QThread):
    frameReceived = Signal(bytes, int, int)
    errorOccurred = Signal(str)

    def __init__(self, buffer_size: int):
        super().__init__()
        self.rx = SharedMemoryReceiver(buffer_size)
        self.running = False

    def run(self):
        self.setPriority(QThread.LowPriority)

        if not self.rx.connect():
            self.errorOccurred.emit("Connect fail")
            return

        self.running = True

        while self.running:
            try:
                result = self.rx.receive()
                if result is not None:
                    data, width, height = result
                    self.frameReceived.emit(data, width, height)
                QThread.usleep(15000)
            except:
                self.rx.close()
                if not self.rx.connect():
                    self.errorOccurred.emit("Reconnect fail")
                    self.running = False

    def stop(self):
        self.running = False
        self.rx.close()
        self.quit()
        self.wait()


class Receiver:
    def __init__(self, buffer_size: int):
        self.thread = ReceiverThread(buffer_size)
        self.thread.errorOccurred.connect(self._on_error)
        self._running = False

    def _on_error(self, text: str):
        logging.warning(f"Receiver error: {text}")

    def start(self):
        if not self._running:
            self.thread.start()
            self._running = True

    def stop(self):
        if self._running:
            self.thread.stop()
            self._running = False


class AccelGraphicsView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent) 
        self.type = "accelgraphicsview"

        self.rx = None
        self.qwidget = ImageViewer()

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
        
        self._runner.event(
            name=self.name,
            type="accelgraphicsview_view_size_changed",
            width=size.width(),
            height=size.height()
        )

    def _handle_input(self, event: dict):

        self._runner.event(
            name=self.name,
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

