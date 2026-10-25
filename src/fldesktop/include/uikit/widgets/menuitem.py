from PySide6.QtGui import QAction
from fldesktop.include.uikit.widgets.base import Widget


class MenuItem(Widget):
    def __init__(self, comm, name, attrs):
        self.qaction = QAction()
        super().__init__(
            comm, name, attrs, {
                "Attr.UI.Widget.MenuItem.Text": ""
            }
        )
        self.type = "menuitem"

        self._setup()

    def reparent(self, parent):

        self.parent = parent

        if hasattr(parent, "qwidget"):
            if parent.type == "menu":
                parent.qwidget.addAction(self.qaction)

    def add_child(self, child):

        return True

    def apply_attrs(self):
        super().apply_attrs()

        self.qaction.setText(self.attrs["Attr.UI.Widget.MenuItem.Text"])