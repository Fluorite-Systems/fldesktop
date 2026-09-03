from fldesktop.include.widgets.flowlayout import FlowLayout
from fldesktop.include.compositor.widgets.base import Widget


class FLayout(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "flayout"
        self.qlayout = FlowLayout()

        self._setup()
