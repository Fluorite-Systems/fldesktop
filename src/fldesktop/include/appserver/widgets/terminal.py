from fldesktop.include.widgets.terminal import Terminal as TerminalWidget
from fldesktop.include.appserver.widgets.base import Widget


class Terminal(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "terminal"
        self.qwidget = TerminalWidget()

        self._setup()
