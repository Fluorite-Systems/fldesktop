from fldesktop.include.widgets.flowlayout import FlowLayout
from fldesktop.include.appserver.widgets.base import Widget


class FLayout(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "flayout"
        self.qlayout = FlowLayout()

        self._setup()
