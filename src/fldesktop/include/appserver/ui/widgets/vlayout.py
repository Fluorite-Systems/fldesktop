from PySide6.QtWidgets import QVBoxLayout
from fldesktop.include.appserver.ui.widgets.base import Widget


class VLayout(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "vlayout"
        self.qlayout = QVBoxLayout()

        self._setup()
