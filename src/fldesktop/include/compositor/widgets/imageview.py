from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImageReader
from PySide6.QtCore import Qt
from fldesktop.include.compositor.widgets.base import Widget

import base64


class ImageView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "imageview"
        self.qwidget = QLabel()

        self.base_props = {
            "image": "",
            "source": "",
            "quality": "fast",
            "keep_aspect_ratio": True,
            "full_cover": False
        }

        self.pixmap = QPixmap()
        self.qwidget.resizeEvent = self.resizeEvent

        self._setup()

    def apply_props(self):
        super().apply_props()

        if self.props["image"]:
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(
                base64.b64decode(self.props["image"].encode())
            )

        if self.props["source"]:
            if self.props["quality"] == "fast":
                reader = QImageReader(self.props["source"])
                reader.setScaledSize(self.qwidget.size().scaled(
                    self.qwidget.size().width(),
                    self.qwidget.size().height(),
                    Qt.KeepAspectRatioByExpanding
                ))
                self.pixmap = QPixmap.fromImage(reader.read())
            else:
                self.pixmap = QPixmap(self.props["source"])
    
        self.resizeEvent(None)

    def resizeEvent(self, ev):
        self.qwidget.setPixmap(
            self.pixmap.scaled(
                self.qwidget.size(),
                (Qt.KeepAspectRatioByExpanding if self.props["full_cover"] \
                    else Qt.KeepAspectRatio) if \
                        self.props["keep_aspect_ratio"] else \
                            Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.FastTransformation if self.props["quality"] == "fast" \
                    else Qt.SmoothTransformation
            )
        )
