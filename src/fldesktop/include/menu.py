from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QObject, QEvent

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.widgets.animation import Animation


class EventFilter(QObject):
    def __init__(self, menu):
        super().__init__()

        self.menu = menu

        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.menu.isVisible():

                click_point = event.globalPosition().toPoint()

                global_top_left = self.menu.mapToGlobal(self.menu.rect().topLeft())


                menu_global_rect = self.menu.rect()
                menu_global_rect.moveTopLeft(global_top_left)

                if menu_global_rect.contains(click_point):
                    return super().eventFilter(obj, event)
                else:
                    self.menu.close_menu()
                    return False 
                
        return super().eventFilter(obj, event)


class Menu(Surface): 
    def __init__(self, comm, widget: QWidget, anchor: QWidget, desktop):
        super().__init__(comm, desktop)
        self.desktop = desktop
        self.anchor = anchor

        self.setFixedSize(widget.size())

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(widget)
        self.setObjectName("menu")

        self.filter = EventFilter(self)

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
            #self.setup_overlay()
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

        #self.overlay.close()
        self.hide()
        #self.move(self.x(), -self.height())
        
        Animation(self.comm, self.parent(), self.grab(), "mclose",
                  {"pos": self.pos(), "size": self.size()},
                  lambda: ...
        )
