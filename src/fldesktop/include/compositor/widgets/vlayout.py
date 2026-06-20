from PySide6.QtWidgets import QVBoxLayout
from fldesktop.include.compositor.widgets.base import Widget


class VLayout(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "vlayout"
        self.qlayout = QVBoxLayout()

        self._setup()
