from fldesktop.include.widgets.terminal import Terminal as TerminalWidget
from fldesktop.include.uikit.widgets.base import Widget


class Terminal(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "terminal"
        self.qwidget = TerminalWidget()

        self._setup()
