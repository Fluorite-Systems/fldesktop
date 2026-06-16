from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import (Qt, QPropertyAnimation, QParallelAnimationGroup,
                            QEasingCurve, QPoint, QSize)


class Animation(QWidget):
    def __init__(self, parent: QWidget, pixmap: QPixmap,
                 type: str, params: dict, on_finished):
        super().__init__(parent)

        self.pixmap = pixmap

        self.show()
        self.raise_()

        self.animate(type, params, on_finished)

    def animate(self, type: str, params: dict, on_finished):
        
        ag = QParallelAnimationGroup(self)
        app = QPropertyAnimation(self, b"pos")
        app.setDuration(150)
        app.setEasingCurve(QEasingCurve.Type.OutQuart)
        aps = QPropertyAnimation(self, b"size")
        aps.setDuration(150)
        aps.setEasingCurve(QEasingCurve.Type.OutQuart)
        ag.addAnimation(app)
        ag.addAnimation(aps)

        ag.finished.connect(
            lambda: self.finished_handler(on_finished)
        )

        if type == "wmaximize":
            app.setStartValue(
                QPoint(
                    params["pos"].x() + 50,
                    params["pos"].y() + 50
                )
            )
            app.setEndValue(params["pos"])
            aps.setStartValue(
                QSize(
                    params["size"].width() - 100,
                    params["size"].height() - 100
                )
            )
            aps.setEndValue(params["size"])

        elif type == "wunmaximize":
            app.setStartValue(
                QPoint(
                    params["pos"].x() - 50,
                    params["pos"].y() - 50
                )
            )
            app.setEndValue(params["pos"])
            aps.setStartValue(
                QSize(
                    params["size"].width() + 100,
                    params["size"].height() + 100
                )
            )
            aps.setEndValue(params["size"])


        elif type == "wminimize":
            app.setStartValue(params["pos"])
            app.setEndValue(
                QPoint(
                    params["pos"].x() // 2,
                    params["pos"].y() // 2
                )
            )
            aps.setStartValue(params["size"])
            aps.setEndValue(QSize(0, 0))

        elif type == "wunminimize":
            app.setStartValue(
                QPoint(
                    params["pos"].x() - 100,
                    params["pos"].y() - 100
                )
            )
            app.setEndValue(params["pos"])
            aps.setStartValue(
                QSize(
                    params["size"].width() - 100,
                    params["size"].height() - 100
                )
            )
            aps.setEndValue(params["size"])

        elif type == "wopen":
            app.setStartValue(
                QPoint(
                    params["pos"].x(),
                    params["pos"].y() + params["size"].width() // 2
                )
            )
            app.setEndValue(params["pos"])
            aps.setStartValue(
                QSize(
                    params["size"].width(), 0
                )
            )
            aps.setEndValue(params["size"])

        elif type == "wclose":
            app.setStartValue(params["pos"])
            app.setEndValue(
                QPoint(
                    params["pos"].x(),
                    params["pos"].y() + params["size"].height() // 2
                )
            )
            aps.setStartValue(params["size"])
            aps.setEndValue(
                QSize(
                    params["size"].width(), 0
                )
            )

        ag.start()

    def finished_handler(self, callback):
        callback()
        self.close()

    def paintEvent(self, event):

        if self.pixmap.isNull():
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        painter.drawPixmap(self.rect(), self.pixmap)
