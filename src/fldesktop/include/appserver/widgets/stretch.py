from fldesktop.include.appserver.widgets.base import Widget


class Stretch(Widget):
    def __init__(self, runner, name, props):
        super().__init__(runner, name, props)
        self.type = "stretch"

        self._setup()
