from PySide6.QtWidgets import QTabWidget, QWidget
from fldesktop.include.uikit.widgets.base import Widget
from fldesktop.include.uikit.widgets.vlayout import VLayout

class Tabs(Widget):
    def __init__(self, runner, name, attrs):
        super().__init__(runner, name, attrs)
        self.type = "tabs"
        self.qwidget = QTabWidget()

        self.tabs = []

        self.callables = {
            "add_tab": self.add_tab
        }

        self._setup()

        self.qwidget.setTabsClosable(True)
        self.qwidget.tabCloseRequested.connect(self.tab_close_handler)

        if "tabs" in self.attrs:
            for i in self.attrs["tabs"]:
                name = self.attrs["tabs"][i]["title"] if "title" in self.attrs["tabs"][i] else str(i)
                p = VLayout(self._runner, str(i), {}, None)
                p._setup()
                self._runner.parser.build_tree_from_objects(self.attrs["tabs"][i]["children"], p)
                w = QWidget()
                w.setLayout(p.qlayout)
                self.qwidget.addTab(w, name)

    def add_tab(self, title: str, children: dict):
        p = VLayout(self._runner, title, {}, None)
        p._setup()
        self._runner.parser.build_tree_from_objects(children, p)
        w = QWidget()
        w.setLayout(p.qlayout)
        self.qwidget.addTab(w, title)

    def tab_close_handler(self, index):
        widget = self.qwidget.widget(index)
