from PySide6.QtWidgets import (QPushButton, QVBoxLayout, QWidget,
                               QScrollArea, QLineEdit, QHBoxLayout,
                               QLabel, QTextEdit)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QSize

from fldesktop.include.menu import Menu


class SearchBtn(QPushButton):
    def __init__(self, comm):
        super().__init__()
        
        self.comm = comm
        
        self.setText(self.comm.request("localemgr", "tr", "Search"))
        self.setIcon(QIcon.fromTheme("search-symbolic"))

        self.search_ui = SearchUI(self.comm)

        self.search_menu = Menu(
            self.comm, self.search_ui, self,
            self.comm.request("desktop", "get_instance")
        )

        self.clicked.connect(self.search_menu.open)
        self.search_ui.close_menu.connect(self.search_menu.close_menu)


class SearchUI(QWidget):
    close_menu = Signal()

    def __init__(self, comm):
        super().__init__()

        self.comm = comm

        self.setFixedSize(500, 400)
        
        self.layout = QVBoxLayout(self)

        self.container = QWidget()
        self.container.layout = QVBoxLayout(self.container)

        self.scroller = QScrollArea(widgetResizable=True)
        self.scroller.setWidget(self.container)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText(
            self.comm.request("localemgr", "tr", "Type here to search...")
        )

        self.layout.addWidget(self.entry)
        self.layout.addWidget(self.scroller)

        self.entry.textChanged.connect(self.query)

        self.query()
    
    def query(self):

        while self.container.layout.count():
            item = self.container.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        text = str(self.entry.text())

        r = self.comm.request("search", "search", text)

        for provider in r:

            self.container.layout.addWidget(QLabel(provider))

            for v in r[provider]:

                if v["type"] == "review":
                    vw = ReviewView(v["text"], v["images"])
                elif v["type"] == "actions":
                    vw = ActionsView(v["actions"])
                elif v["type"] == "items":
                    for i in v["items"]:
                        i["callback"] = lambda _, c=i["callback"]:\
                            self.callback_handler(c)
                    vw = ItemView(v["items"])
                
                self.container.layout.addWidget(vw)
        
        self.container.layout.addStretch()
    
    def callback_handler(self, callback):
        self.close_menu.emit()
        callback()


class ReviewView(QWidget):
    def __init__(self, text: str, images: list):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.text = QTextEdit(text)
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.WidgetWidth)

        if images:
            self.img_scroller = QScrollArea(widgetResizable=True)
            self.img_container = QWidget()
            self.img_scroller.setWidget(self.img_container)
            self.img_layout = QHBoxLayout(self.img_container)
            self.layout.addWidget(self.img_scroller)

        self.layout.addWidget(self.text)


class ActionsView(QWidget):
    def __init__(self, actions: list):
        super().__init__()

        self.layout = QVBoxLayout(self)

        for i in actions:
            self.layout.addWidget(
                Action(i["title"], i["icon"], i["callback"])
            )


class ItemView(QWidget):
    def __init__(self, items: list):
        super().__init__()

        self.layout = QVBoxLayout(self)

        for i in items:
            self.layout.addWidget(
                Item(i["title"], i["description"], i["icon"], i["callback"])
            )


class Action(QPushButton):
    def __init__(self, title: str, icon: QIcon, callback):
        super().__init__()

        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setText(title)
        self.clicked.connect(callback)

        # temporary solution, make custom layout later


class Item(QPushButton):
    def __init__(self, title: str, desc: str,
                icon: QIcon, callback):
        super().__init__()

        self.setMinimumHeight(64)

        self.layout = QHBoxLayout(self)
        self.text_layout = QVBoxLayout()
        
        self.icon = QLabel()
        self.icon.setPixmap(icon.pixmap(48, 48))
        self.title = QLabel(title)
        self.title.setWordWrap(True)
        self.desc = QLabel(desc)

        self.layout.addWidget(self.icon)
        self.layout.addLayout(self.text_layout)
        self.text_layout.addWidget(self.title)
        self.text_layout.addWidget(self.desc)
        self.layout.addStretch()

        self.clicked.connect(callback)
