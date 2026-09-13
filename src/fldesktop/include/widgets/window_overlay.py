from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolButton
from PySide6.QtCore import Qt, QPoint, QSize

from fldesktop.include.widgets.surface import Surface


class Container(QWidget):
    def __init__(self, callback):
        super().__init__()

        self.callback = callback

    def resizeEvent(self, event):
        self.callback()
        return super().resizeEvent(event)


class OverlayView(Surface):
    def __init__(self, parent, comm):
        super().__init__(comm, parent, tint=1)

        self.setMinimumSize(200, 100)

        self.set_raycast_enabled(False)

        self.ml = QVBoxLayout(self)
        self.tl = QHBoxLayout()
        self.cont = Container(parent.on_resize)

        self.ml.addLayout(self.tl)

        self.close_btn = QToolButton(
            icon=comm.request("iconmgr", "get", "window-close")
        )
        self.close_btn.setObjectName("flatbtn")
        self.close_btn.setFixedSize(24, 24)

        self.tl.addStretch()
        self.tl.addWidget(self.close_btn)

        self.ml.addStretch()
        self.ml.addWidget(self.cont)
        self.ml.addStretch()


class WindowOverlay(QWidget):
    def __init__(self, comm, winid):
        super().__init__()

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.comm = comm
        self.winid = winid

        self.view = OverlayView(self, comm)

        self.view.move(
            QPoint(
                (self.width() - self.view.width()) // 2,
                (self.height() - self.view.height()) // 2
            )
        )

    def on_resize(self):
        self.view.move(
            QPoint(
                (self.width() - self.view.width()) // 2,
                (self.height() - self.view.height()) // 2
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.on_resize()

    def close(self):
        self.view.close()
        self.comm.request("wm", "rm_window_overlay", self.winid, self, False)
        super().close()