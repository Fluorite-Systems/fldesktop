from cmath import phase

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QPushButton,
                               QSizePolicy, QLabel, QFrame)
from PySide6.QtCore import Qt

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.appletmgr.applet import Applet
from fldesktop.include.widgets.animation import Animation


class Sidebar(Surface):
    def __init__(self, comm):
        super().__init__(
            comm,
            comm.request("desktop", "get_instance"),
            5
        )

        self.comm = comm
        self.comm.subscribe("desktop_size_changed", self.update_geometry)

        self.mlayout = QVBoxLayout(self)

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

        self.applets = []

        self.update_geometry()

    def update_geometry(self):

        self.setFixedSize(175, self.parent().height() - 26)
        self.move(self.parent().width() - self.width(), 26)

    def add_applet(self, applet: Applet):

        self.applets.append(applet)
        if self.isVisible():
            self.applets_layout.addWidget(applet.widget)

    def del_applet(self, applet: Applet):

        if self.isVisible():
            index = self.applets_layout.indexOf(applet) + 1
            if index < self.applets_layout.count():
                self.applets_layout.itemAt(index).widget().close()
        self.applets.remove(applet)

    def show(self):
        def phase2(self):
            super().show()
            self.comm.request("panel", "raise")
        
        for i in self.applets:
            #l = QLabel("applet idk")
            #self.applets_layout.addWidget(l)
            self.applets_layout.addWidget(i.widget)
            if i is not self.applets[-1]:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                #line.setFrameShadow(QFrame.Shadow.Sunken)
                self.applets_layout.addWidget(line)

        Animation(
            self.comm, self.parent(), self.grab(), "sbopen",
            {"pos": self.pos(), "size": self.size()},
            lambda s=self: phase2(s)
        )
        

    def hide(self):
        for i in self.applets:
            i.widget.setParent(None)
        for i in range(self.applets_layout.count()):
            w = self.applets_layout.itemAt(i).widget()
            w.close()
            w.deleteLater()
        Animation(
            self.comm, self.parent(), self.grab(), "sbclose",
            {"pos": self.pos(), "size": self.size()}, lambda: ...
        )
        super().hide()