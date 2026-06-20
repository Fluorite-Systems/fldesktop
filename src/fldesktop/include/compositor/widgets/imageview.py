from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImageReader
from PySide6.QtCore import Qt
from fldesktop.include.compositor.widgets.base import Widget


class ImageView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "imageview"
        self.qwidget = QLabel()

        self.callables = {
            "set_image": self.set_image,
            "set_source": self.set_source
        }

        self._setup()

        self.quality = "good"

        if "quality" in props:
            if props["quality"] == "fast":
                self.quality = "fast"

        self.pixmap = QPixmap()
        self.qwidget.resizeEvent = self.resizeEvent

    def set_image(self, image: str) -> None:
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(base64.b64decode(image.encode()))
        self.resizeEvent(None)

    def set_source(self, source: str) -> None:

        if self.quality == "fast":
            reader = QImageReader(source)
            reader.setScaledSize(self.qwidget.size().scaled(
                self.qwidget.size().width(),
                self.qwidget.size().height(),
                Qt.KeepAspectRatioByExpanding
            ))
            self.pixmap = QPixmap.fromImage(reader.read())
        else:
            self.pixmap = QPixmap(source)

        self.resizeEvent(None)

    def resizeEvent(self, ev):
        self.qwidget.setPixmap(
            self.pixmap.scaled(
                self.qwidget.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.FastTransformation if self.quality == "fast" else \
                    Qt.SmoothTransformation
            )
        )
