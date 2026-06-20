from PySide6.QtWidgets import QTreeView, QFileSystemModel
from PySide6.QtCore import QDir
from fldesktop.include.compositor.widgets.base import Widget


class FileTree(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "filetree"
        self.qwidget = QTreeView()

        self.callables = {
            "set_path": self.set_path
        }

        self._setup()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        self.qwidget.setModel(self.model)

        self.qwidget.doubleClicked.connect(self.on_doubleclick)

        self.set_path("/home/romario/")

    def set_path(self, path: str):
        print("got path", path)
        index = self.model.index(path)

        if self.model.isDir(index):
            self.qwidget.setRootIndex(index)

    def on_doubleclick(self, index):
        path = self.model.filePath(index)
        self._runner.event(
            name=self.name, type="filetree_doubleclick",
            path=str(path)
        )
