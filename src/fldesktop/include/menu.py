from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import (QPropertyAnimation, QEasingCurve,
                            QPoint, Qt, QParallelAnimationGroup)

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.widgets.animation import Animation


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

        def show(self):
            self.show()
            self.desktop.panel.raise_()
            self.setup_overlay()
            self.raise_()

        x = int(self.anchor.x() - \
                    (self.size().width() - self.anchor.size().width()) / 2)
        if x < 0:
            x = 4
        if x > self.desktop.size().width() - self.size().width():
            x = self.desktop.size().width() - self.size().width() - 4

        self.move(x, 30)

        Animation(self.comm, self.parent(), self.grab(), "mopen",
                  {"pos": self.pos(), "size": self.size()},
                  lambda: show(self))

    def close_menu(self):
        "Close the menu with some anim"

        self.overlay.close()
        self.hide()

        #self.move(self.x(), -self.height())
        
        Animation(self.comm, self.parent(), self.grab(), "mclose",
                  {"pos": self.pos(), "size": self.size()},
                  lambda: ...
        )
