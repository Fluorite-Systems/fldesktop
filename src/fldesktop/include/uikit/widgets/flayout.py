from fldesktop.include.widgets.flowlayout import FlowLayout
from fldesktop.include.uikit.widgets.base import Widget


class FLayout(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "flayout"
        self.qlayout = FlowLayout()

        self._setup()
