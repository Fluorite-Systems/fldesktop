from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import (QPropertyAnimation, QEasingCurve,
                            QPoint, Qt, QParallelAnimationGroup)

from fldesktop.include.widgets.surface import Surface


class Overlay(QWidget):
    def __init__(self, desktop, menu: QWidget):
        super().__init__(desktop)

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, 
                        False)
        
        self.setFixedSize(desktop.size())

        self.menu = menu

    def mousePressEvent(self, event):
        self.menu.close_menu()
        return super().mousePressEvent(event)



class Menu(Surface): 
    def __init__(self, comm, widget: QWidget, anchor: QWidget, desktop):
        super().__init__(comm, desktop)
        self.desktop = desktop
        self.anchor = anchor

        self.setFixedSize(widget.size())

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(3)
        self.shadow.setYOffset(4)
        self.shadow.setColor(Qt.black)
        #self.setGraphicsEffect(self.shadow)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(widget)

        self.setObjectName("menu")

        self.hide()
        self.lower()

    def setup_overlay(self):
        "Creates overlay"

        self.overlay = Overlay(self.desktop, self)
        self.overlay.show()
        self.overlay.raise_()

    def open(self):
        "Opens menu with some anim"
        self.show()
        self.raise_()
        self.desktop.panel.raise_()
        self.setup_overlay()

        x = int(self.anchor.x() - \
                    (self.size().width() - self.anchor.size().width()) / 2)
        if x < 0:
            x = 4
        if x > self.desktop.size().width() - self.size().width():
            x = self.desktop.size().width() - self.size().width() - 4

        y = 30

        self.move(x, -self.size().height())

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setEndValue(QPoint(x, y))
        self.anim.setDuration(350)
        self.anim.finished.connect(self.raise_)
        self.anim.start()
    
    def close_menu(self):
        "Close the menu with some anim"

        self.overlay.close()
        self.desktop.panel.raise_()

        y = -self.size().height()

        self.anim = QParallelAnimationGroup()

        self.anim1 = QPropertyAnimation(self, b"pos")
        self.anim1.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim1.setEndValue(QPoint(self.x(), y))
        self.anim1.setDuration(350)

        #self.anim2 = QPropertyAnimation(self, b"opacity")
        #self.anim2.setEasingCurve(QEasingCurve.Type.InCubic)
        #self.anim2.setEndValue(0.0)
        ##self.anim2.setDuration(350)

        self.anim.addAnimation(self.anim1)
        #self.anim.addAnimation(self.anim2)
        self.anim.finished.connect(self.hide)
        self.anim.start()
