from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                               QPushButton)


class SidebarItem(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFlat(True)

        self.prev_text = ""


class Sidebar(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.scroller = QScrollArea(widgetResizable=True)
        self.scrollable = QWidget()
        self.scroller.setWidget(self.scrollable)
        self.layout.addWidget(self.scroller)

        self.item_layout = QVBoxLayout(self.scroller)
        self.item_layout.addStretch()

        self.setFixedWidth(200)

        self.expanded = True
    
    def add_item(self, item: SidebarItem):
        self.item_layout.insertWidget(0, item)
    
    def expand(self):
        for i in range(self.item_layout.count()):
            w = self.item_layout.itemAt(i).widget()
            if w and type(w) == SidebarItem:
                w.setText(w.prev_text)
        
        self.setFixedWidth(200)

        self.expanded = True
    
    def shrink(self):
        
        for i in range(self.item_layout.count()):
            w = self.item_layout.itemAt(i).widget()
            if w and type(w) == SidebarItem:
                w.prev_text = w.text()
                w.setText("")

        self.setFixedWidth(64)

        self.expanded = False
    
    def refresh(self, size):

        self.setFixedHeight(size.height() - 30)

        if size.width() >= 700:
            if not self.expanded:
                self.expand()
        else:
            if self.expanded:
                self.shrink()