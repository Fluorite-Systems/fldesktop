from PySide6.QtWidgets import QVBoxLayout
from fldesktop.include.appserver.widgets.base import Widget


class VLayout(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "vlayout"
        self.qlayout = QVBoxLayout()

        self._setup()
