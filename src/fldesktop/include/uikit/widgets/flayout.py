from fldesktop.include.widgets.flowlayout import FlowLayout
from fldesktop.include.uikit.widgets.base import Widget


class FLayout(Widget):
    def __init__(self, comm, name, attrs):
        self.qlayout = FlowLayout()
        super().__init__(comm, name, attrs)
        self.type = "flayout"

        self._setup()
