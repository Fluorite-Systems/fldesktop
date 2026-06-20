from fldesktop.include.compositor.widgets.base import Widget


class RootWidget(Widget):
    def __init__(self, runner):
        super().__init__(runner, "root", {}, None)
        self.type = "app"

        self._setup()
        self.qlayout = runner.main_layout
