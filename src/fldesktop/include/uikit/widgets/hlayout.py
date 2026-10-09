from PySide6.QtWidgets import QHBoxLayout
from fldesktop.include.uikit.widgets.base import Widget


class HLayout(Widget):
    def __init__(self, comm, name, attrs):
        self.qlayout = QHBoxLayout()
        super().__init__(comm, name, attrs)
        self.type = "hlayout"

        self._setup()
