from PySide6.QtWidgets import QVBoxLayout
from fldesktop.include.uikit.widgets.base import Widget


class VLayout(Widget):
    def __init__(self, comm, name, attrs):
        self.qlayout = QVBoxLayout()
        super().__init__(comm, name, attrs)
        self.type = "vlayout"

        self._setup()
