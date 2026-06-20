from fldesktop.include.widgets.terminal import Terminal as TerminalWidget
from fldesktop.include.compositor.widgets.base import Widget


class Terminal(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "terminal"
        self.qwidget = TerminalWidget()

        self._setup()
