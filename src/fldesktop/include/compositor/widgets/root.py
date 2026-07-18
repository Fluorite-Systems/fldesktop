from PySide6.QtWidgets import QVBoxLayout
from fldesktop.include.compositor.widgets.base import Widget


class RootWidget(Widget):
    def __init__(self, runner):
        super().__init__(runner, "root", {}, None)
        self.type = "app"
        self.qlayout = QVBoxLayout()

        self._setup()
        runner.main_layout.addLayout(self.qlayout)
