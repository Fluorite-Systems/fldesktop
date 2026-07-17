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

                menu_global_rect = self.menu.rect()
                menu_global_rect.moveTopLeft(
                    self.menu.mapToGlobal(self.menu.rect().topLeft())
                )

                anchor_global_rect = self.menu.anchor.rect()
                anchor_global_rect.moveTopLeft(
                    self.menu.anchor.mapToGlobal(
                        self.menu.anchor.rect().topLeft()
                    )
                )

                if menu_global_rect.contains(click_point):
                    return super().eventFilter(obj, event)
                elif anchor_global_rect.contains(click_point):
                    return False
                else:
                    self.menu.close_menu()
                    return False 
                
        return super().eventFilter(obj, event)


class Menu(Surface): 
    def __init__(self, comm, widget: QWidget, anchor: QWidget, desktop):
        super().__init__(comm, desktop)
        self.desktop = desktop
        self.anchor = anchor
        self.active = False

        self.setFixedSize(widget.size())

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(widget)
        self.setObjectName("menu")

        self.filter = EventFilter(self)

        self.hide()
        self.lower()

    def open(self):
        "Opens menu with some anim"

        def show(self): 
            if self.comm.request("lockscreen", "is_visible"):
                self.comm.send("lockscreen", "raise")
                self.show()
                self.raise_()
                self.comm.send("lockscreen", "raise_qc_btn")
            else:
                self.show()
                self.desktop.panel.raise_()
                self.raise_()

        if self.isVisible():
            self.close_menu()
            return

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

        self.hide()        
        
        Animation(self.comm, self.parent(), self.grab(), "mclose",
                  {"pos": self.pos(), "size": self.size()},
                  lambda: ...
        )
