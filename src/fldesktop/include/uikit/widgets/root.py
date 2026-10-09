from PySide6.QtWidgets import QVBoxLayout
from fldesktop.include.uikit.widgets.base import Widget


class RootWidget(Widget):
    def __init__(self, runner):
        self.qlayout = QVBoxLayout()
        super().__init__(runner, "root", {}, None)
        self.type = "app"

        self._setup()
        runner.main_layout.addLayout(self.qlayout)
