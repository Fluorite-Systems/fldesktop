from fldesktop.include.widgets.isolated_webengine import IQWebEngineView
from fldesktop.include.compositor.widgets.base import Widget


class WebView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "webview"
        self.qwidget = IQWebEngineView()

        self.callables = {
            "load_page": self.load_page,
            "reload": self.reload,
            "forward": self.forward,
            "back": self.back
        }

        self._setup()

        IQWebEngineView().titleChanged.connect(
            lambda t: self._runner.event(
            type="webview_page_title_changed", name=self.name,
            title=t)
        )

    def load_page(self, page: str):
        self.qwidget.setUrl(page)

    def reload(self) -> None:
        self.qwidget.reload()

    def forward(self) -> None:
        self.qwidget.forward()

    def back(self) -> None:
        self.qwidget.back()
