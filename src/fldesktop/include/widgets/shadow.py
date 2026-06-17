from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, QPoint, QSize

from pathlib import Path

class Shadow(QPushButton): # QPushButton because it works
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent) 

        self.path = Path(__file__).resolve().parent.parent\
            / "assets" / "shadow.png"

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StaticContents, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName("Shadow")
               
        self.setStyleSheet(f"""
            #Shadow {{
                border-image: url({self.path}) 25 31 33 26 stretch;
                border-width: 25px 31px 33px 26px;
                background-color: transparent;
            }}
        """)

        self.hide()

    def move(self, pos: QPoint) -> None:
        super().move(
            QPoint(
                pos.x() - 26,
                pos.y() - 25
            )
        )

    def resize(self, size: QSize) -> None:
        super().resize(
            QSize(
                size.width() + 26 + 31,
                size.height() + 25 + 33
            )
        )
