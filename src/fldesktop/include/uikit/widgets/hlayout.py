from PySide6.QtWidgets import QHBoxLayout
from fldesktop.include.uikit.widgets.base import Widget


class HLayout(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "hlayout"
        self.qlayout = QHBoxLayout()

        self._setup()
