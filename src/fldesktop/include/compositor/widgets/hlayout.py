from PySide6.QtWidgets import QHBoxLayout
from fldesktop.include.compositor.widgets.base import Widget


class HLayout(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "hlayout"
        self.qlayout = QHBoxLayout()

        self._setup()
