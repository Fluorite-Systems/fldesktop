from fldesktop.include.compositor.widgets.base import Widget


class Stretch(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "stretch"

        self._setup()
