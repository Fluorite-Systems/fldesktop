from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (QPropertyAnimation, QEasingCurve,
                            QEventLoop, Property)
from PySide6.QtGui import QPalette, QColor


class FadeEffect(QWidget):
    def __init__(self, comm, parent: QWidget):
        super().__init__(parent)

        self.comm = comm
        self.comm.register("fade_effect", {
                "fadein": self.fadein,
                "fadeout": self.fadeout
            }
        )

        self.setAutoFillBackground(True)

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        self.setPalette(pal)

        self.fi_anim = QPropertyAnimation(self, b"currentColor")
        self.fi_anim.setDuration(500)
        self.fi_anim.setStartValue(QColor(0, 0, 0, 255))
        self.fi_anim.setEndValue(QColor(0, 0, 0, 0))

        self.fi_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fi_anim.finished.connect(self.hide)

        self.fo_anim = QPropertyAnimation(self, b"currentColor")
        self.fo_anim.setDuration(500)
        self.fo_anim.setStartValue(QColor(0, 0, 0, 0))
        self.fo_anim.setEndValue(QColor(0, 0, 0, 255))

        self.fo_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self.loop = QEventLoop()
        self.fo_anim.finished.connect(self.loop.exit)

    @Property(QColor)
    def currentColor(self) -> QColor:
        return self.palette().color(QPalette.ColorRole.Window)

    @currentColor.setter
    def currentColor(self, color: QColor):
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(pal)

    def _prepare_geometry(self) -> None:
        "Prepare overlay geometry based on the desktop size"

        d = self.comm.request("desktop", "get_instance")
        self.setFixedSize(d.size())
        self.move(0, 0)
        self.show()
        self.raise_()

    def fadein(self) -> None:
        "Fade in effect"

        self._prepare_geometry()

        self.fi_anim.start()

    def fadeout(self) -> None:
        "Fade out effect"

        self._prepare_geometry()

        self.fo_anim.start()
        self.loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
