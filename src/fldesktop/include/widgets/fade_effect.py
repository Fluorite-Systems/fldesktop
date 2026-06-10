from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class FadeEffect(QWidget):
    def __init__(self, comm, parent: QWidget):
        super().__init__(parent)

        self.comm = comm
        self.comm.register("fade_effect", {
                "fadein": self.fadein,
                "fadeout": self.fadeout
            }
        )

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: black")

        self.effect = QGraphicsOpacityEffect(self)
        self.effect.setOpacity(1.0)
        self.setGraphicsEffect(self.effect)

        self.fi_anim = QPropertyAnimation(self.effect, b"opacity")
        self.fi_anim.setStartValue(1.0)
        self.fi_anim.setEndValue(0.0)
        self.fi_anim.setDuration(500)
        self.fi_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fi_anim.finished.connect(self.hide)

        self.fo_anim = QPropertyAnimation(self.effect, b"opacity")
        self.fo_anim.setStartValue(0.0)
        self.fo_anim.setEndValue(1.0)
        self.fi_anim.setDuration(500)
        self.fi_anim.setEasingCurve(QEasingCurve.Type.InCubic)
    
    def fadein(self):
        d = self.comm.request("desktop", "get_instance")
        self.setFixedSize(d.size())
        self.move(0, 0)

        self.show()
        self.raise_()
        self.fi_anim.start()

    def fadeout(self, callback = None):

        if callback:
            self.fo_anim.finished.connect(callback)
        
        d = self.comm.request("desktop", "get_instance")
        self.setFixedSize(d.size())

        self.show()
        self.raise_()
        self.fo_anim.start()