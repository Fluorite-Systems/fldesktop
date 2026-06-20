from PySide6.QtWidgets import QListView
from fldesktop.include.compositor.widgets.base import Widget


class ListView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "listview"
        self.qwidget = QListView()

        self.callables = {
            "set_contents": self.set_contents
        }

        self._setup()

        self.qwidget.setViewMode(QListView.ViewMode.IconMode)
        self.qwidget.setIconSize(QSize(64, 64))
        self.qwidget.setGridSize(QSize(100, 100))
        self.qwidget.setResizeMode(QListView.ResizeMode.Adjust)
        self.qwidget.setMovement(QListView.Movement.Snap)
        self.qwidget.setSelectionRectVisible(True)
        self.qwidget.setSelectionMode(QListView.ExtendedSelection)
        self.qwidget.setSelectionBehavior(QListView.SelectItems)
        self.qwidget.setEditTriggers(QListView.EditTrigger.NoEditTriggers)

        self.qwidget.doubleClicked.connect(self.doubleclick_handler)

    def set_contents(self, contents: dict):
        model = QStandardItemModel()

        print(contents)

        for name, item in contents.items():
            if type(item) != dict:
                continue

            if "title" in item:
                title = str(item["title"])
            else:
                title = ""

            if "icon" in item:
                icon = QIcon.fromTheme(str(item["icon"]))
            else:
                icon = QIcon.fromTheme("none")

            qitem = QStandardItem(title)
            qitem.setIcon(icon)
            qitem.setData(name, Qt.ItemDataRole.UserRole + 1)

            model.appendRow(qitem)

        self.qwidget.setModel(model)

    def doubleclick_handler(self, index):

        item = self.qwidget.model().itemFromIndex(index)
        id = item.data(Qt.ItemDataRole.UserRole + 1)
        self._runner.event(
            name=id, type="listview_doubleclick"
        )
