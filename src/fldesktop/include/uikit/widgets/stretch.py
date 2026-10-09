from fldesktop.include.uikit.widgets.base import Widget


class Stretch(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "stretch"

        self._setup()
