from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QPushButton,
                               QSizePolicy, QLabel, QFrame)
from PySide6.QtCore import Qt

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.uikit.applet import Applet
from fldesktop.include.widgets.animation import Animation


class Sidebar(Surface):
    def __init__(self, comm):
        super().__init__(
            comm, tint_color=(0, 0, 0), tint_alpha=1,
            layer=3, layer_lock=True, hover_materialize=True
        )

        self.comm = comm
        self.comm.subscribe("desktop_size_changed", self.update_geometry)

        self.mlayout = QVBoxLayout(self)
        self.mlayout.setContentsMargins(0, 0, 0, 0)

        self.scroller = QScrollArea()
        self.scroller.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroller.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroller.setStyleSheet("QScrollArea { border: none; }")


        self.scrollable = QWidget()
        self.scroller.setWidget(self.scrollable)
        self.scroller.setWidgetResizable(True)
        self.mlayout.addWidget(self.scroller)

        self.applets_layout = QVBoxLayout(self.scrollable)
        self.applets_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.applets = []

        self.attach()
        self.update_geometry()

    def update_geometry(self):

        if not self.parent(): return

        self.setFixedSize(175, self.parent().height())
        self.move(self.parent().width() - self.width(), 0)

    def add_applet(self, applet: Applet):

        self.applets.append(applet)
        self.reattach_applets()

    def del_applet(self, applet: Applet):

        self.applets.remove(applet)
        applet.close()
        self.reattach_applets()

    def show(self, disable_anim: bool = False):
        def phase2(self):
            super().show()
            self.comm.request("panel", "raise")
        
        self.attach_applets()

        if disable_anim:
            phase2(self)
            return

        Animation(
            self.comm, self.parent(), self.grab(), "sbopen",
            {"pos": self.pos(), "size": self.size(),
             "tint_color": (0, 0, 0), "tint_alpha": 1},
            lambda s=self: phase2(s)
        )        

    def hide(self):

        self.detach_applets()

        Animation(
            self.comm, self.parent(), self.grab(), "sbclose",
            {"pos": self.pos(), "size": self.size(),
             "tint_color": (0, 0, 0), "tint_alpha": 1}, lambda: ...
        )
        super().hide()

    def attach_applets(self):

        for i in self.applets:
            #l = QLabel("applet idk")
            #self.applets_layout.addWidget(l)
            self.applets_layout.addWidget(i.widget)
            if i is not self.applets[-1]:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                #line.setFrameShadow(QFrame.Shadow.Sunken)
                self.applets_layout.addWidget(line)

    def detach_applets(self):

        for i in self.applets:
            i.widget.setParent(None)
        for i in range(self.applets_layout.count()):
            w = self.applets_layout.itemAt(i).widget()
            w.close()
            w.deleteLater()

    def reattach_applets(self):

        self.detach_applets()
        self.attach_applets()