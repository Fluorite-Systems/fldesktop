from PySide6.QtWidgets import QMenuBar, QSizePolicy
from fldesktop.include.uikit.widgets.base import Widget


class MenuBar(Widget):
    def __init__(self, comm, name, attrs):
        self.qwidget = QMenuBar()
        self.qwidget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Fixed)
        super().__init__(comm, name, attrs)
        self.type = "menubar"

        self._setup()

    def add_child(self, child: Widget):

        return True