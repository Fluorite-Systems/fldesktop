from PySide6.QtWidgets import QTabWidget
from fldesktop.include.compositor.widgets.base import Widget


class Tabs(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "tabs"
        self.qwidget = QTabWidget()

        self.tabs = []

        self._setup()

        if "tabs" in self.props:
            for i in self.props["tabs"]:
                name = self.props["tabs"][i]["title"] if "title" in self.props["tabs"][i] else str(i)
                p = Container(self._runner, str(i), self.props["tabs"][i], {}, self)
                self._runner.parser.build_tree_from_objects(self.props["tabs"][i]["children"], p)
                self.qwidget.addTab(p.qwidget, name)

    def add_tab(self, name: str, props: dict):
        p = Container(self._runner, name, props, {}, self)
        self._runner.parser.build_tree_from_objects(props["children"], p)
        self.qwidget.addTab(p.qwidget, props["title"])
