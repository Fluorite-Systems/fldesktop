from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImageReader
from PySide6.QtCore import Qt
from fldesktop.include.uikit.widgets.base import Widget

import base64


class ImageView(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QLabel()

        super().__init__(
            comm, name, attrs,
            {
                "Attr.UI.Widget.ImageView.Image": "",
                "Attr.UI.Widget.ImageView.Source": "",
                "Attr.UI.Widget.ImageView.Quality": "fast",
                "Attr.UI.Widget.ImageView.KeepAspectRatio": True,
                "Attr.UI.Widget.ImageView.FullCover": False
            }
        )

        self.type = "imageview"        

        self.pixmap = QPixmap()
        self.qwidget.resizeEvent = self.resizeEvent

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        if self.attrs["Attr.UI.Widget.ImageView.Image"]:
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(
                base64.b64decode(
                    self.attrs["Attr.UI.Widget.ImageView.Image"].encode()
                )
            )

        if self.attrs["Attr.UI.Widget.ImageView.Source"]:
            if self.attrs["Attr.UI.Widget.ImageView.Quality"] == "fast":
                reader = QImageReader(
                    self.attrs["Attr.UI.Widget.ImageView.Source"]
                )
                reader.setScaledSize(self.qwidget.size().scaled(
                    self.qwidget.size().width(),
                    self.qwidget.size().height(),
                    Qt.KeepAspectRatioByExpanding
                ))
                self.pixmap = QPixmap.fromImage(reader.read())
            else:
                self.pixmap = QPixmap(
                    self.attrs["Attr.UI.Widget.ImageView.Source"]
                )
    
        self.resizeEvent(None)

    def resizeEvent(self, ev):
        self.qwidget.setPixmap(
            self.pixmap.scaled(
                self.qwidget.size(),
                (Qt.KeepAspectRatioByExpanding if \
                self.attrs["Attr.UI.Widget.ImageView.FullCover"] \
                else Qt.KeepAspectRatio) if \
                self.attrs["Attr.UI.Widget.ImageView.KeepAspectRatio"] else \
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.FastTransformation if \
                self.attrs["Attr.UI.Widget.ImageView.Quality"] == "fast" \
                else Qt.SmoothTransformation
            )
        )
