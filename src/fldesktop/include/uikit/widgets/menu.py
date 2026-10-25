from PySide6.QtWidgets import QMenu, QWidgetAction
from PySide6.QtCore import Qt
from fldesktop.include.uikit.widgets.base import Widget


class Menu(Widget):
    def __init__(self, comm, name, attrs):
        self.qwidget = QMenu()
        super().__init__(
            comm, name, attrs, {
                "Attr.UI.Widget.Menu.Text": ""
            }
        )
        self.type = "menu"

        self._setup()

    def reparent(self, parent):

        self.parent = parent

        if hasattr(parent, "qwidget"):
            if parent.type in ("menubar", "menu"):
                parent.qwidget.addMenu(self.qwidget)
            else:
                parent.qwidget.setContextMenuPolicy(
                    Qt.ContextMenuPolicy.CustomContextMenu
                )
                parent.qwidget.customContextMenuRequested.connect(
                    lambda: self.qwidget.exec(
                        parent.qwidget.mapToGlobal(
                            parent.qwidget.rect().bottomLeft()
                        )
                    )
                )

    def add_child(self, child):

        if hasattr(child, "qwidget"):
            if child.type == "menu":
                self.qwidget.addMenu(child.qwidget)
            else:
                qwc = QWidgetAction(self.qwidget)
                qwc.setDefaultWidget(child.qwidget)
                self.qwidget.addAction(qwc)

    def apply_attrs(self):
        super().apply_attrs()

        self.qwidget.setTitle(self.attrs["Attr.UI.Widget.Menu.Text"])