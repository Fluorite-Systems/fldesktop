from PySide6.QtWebEngineWidgets import QWebEngineView
from fldesktop.include.widgets.isolator import GraphicsIsolatedWidget


class IQWebEngineView(GraphicsIsolatedWidget):
    def __init__(self):
        self.engine = QWebEngineView()
        super().__init__(self.engine)

        for i in dir(self.engine):
            if not hasattr(self, i):
                setattr(self, i, getattr(self.engine, i))