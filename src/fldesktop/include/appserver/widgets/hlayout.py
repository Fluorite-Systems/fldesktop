from PySide6.QtWidgets import QHBoxLayout
from fldesktop.include.appserver.widgets.base import Widget


class HLayout(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "hlayout"
        self.qlayout = QHBoxLayout()

        self._setup()
