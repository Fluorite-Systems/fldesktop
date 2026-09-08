from PySide6.QtGui import QPalette, QColor, QIcon, QFont
from PySide6.QtWidgets import QApplication


STYLESHEET = """
              QWidget#surface
              {
                background-color: rgba(0, 0, 0, 200);
              }

              QWidget#panel
              {
                background-color: black;
              }

              QWidget#menu
              {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 13;
              }

              QWidget#dock
              {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 13;
                padding: 1;
              }

              QPushButton#traybtn
              {
                border: 1;
                background-color: rgba(0, 0, 0, 0);
                padding: 5px;
                margin: 0px;
              }

              QPushButton#traybtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
              }

              QPushButton#traybtn::pressed
              {
                background-color: rgba(255, 255, 255, 25);
              }

              QToolButton#flatbtn
              {
                border: 1;
                background-color: rgba(0, 0, 0, 0);
                padding: 0px;
                margin: 0px;
              }

              QToolButton#flatbtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
              }

              QToolButton#flatbtn::pressed
              {
                background-color: rgba(0, 0, 0, 100);
              }

              QPushButton#taskbarbtn
              {
                border: 1;
                background-color: rgba(0, 0, 0, 0);
                padding-left: 7;
                padding-right: 7
              }

              QPushButton#taskbarbtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
                border-radius: 25;
              }

              QPushButton#taskbarbtn::pressed
              {
                border-bottom: 2px solid white;
              }

              QTextEdit
              {
                background-color: transparent
              }

              QTextBrowser
              {
                background-color: transparent
              }

              QLineEdit
              {
                background-color: transparent
              }
"""

FLUORITE_CS = {
    "Window": "#232629",
    "WindowText": "#f2f4f7",
    "Base": "#2a2e32",
    "AlternateBase": "#30353a",
    "ToolTipBase": "#2f3438",
    "ToolTipText": "#f2f4f7",
    "PlaceholderText": "#9aa3ab",
    "Text": "#f2f4f7",
    "Button": "#2a2e32",
    "ButtonText": "#f2f4f7",
    "BrightText": "#ffffff",
    "Highlight": "#4a86e8",
    "HighlightedText": "#ffffff",
    "Light": "#34393e",
    "Midlight": "#2f3438",
    "Dark": "#181b1f",
    "Mid": "#555b61",
    "Shadow": "#0d0f12",
    "Link": "#2980b9",
    "LinkVisited": "#9b59b6"
}


STD_COLORS = {
    "white": "#f2f4f7",
    "lightwhite": "#FFFFFF",
    "darkwhite": "#D5D8DD",

    "black": "#2a2e32",
    "lightblack": "#4A5056",
    "darkblack": "#121416",

    "red": "#D95C5C",
    "lightred": "#F28B82",
    "darkred": "#A93B3B",

    "orange": "#E89A4A",
    "lightorange": "#F5C27B",
    "darkorange": "#C17A2E",

    "yellow": "#E0B84D",
    "lightyellow": "#F5DC7A",
    "darkyellow": "#B89330",

    "green": "#43B77A",
    "lightgreen": "#78DBA3",
    "darkgreen": "#2A8F5C",

    "teal": "#5AA7A2",
    "lightteal": "#8ACAC5",
    "darkteal": "#3E807B",

    "blue": "#4A86E8",
    "lightblue": "#7BA9F0",
    "darkblue": "#2E62B8",

    "indigo": "#6673C6",
    "lightindigo": "#939DDA",
    "darkindigo": "#4A56A0",

    "purple": "#9575CD",
    "lightpurple": "#B99FD9",
    "darkpurple": "#7657A8",

    "pink": "#CB6A9E",
    "lightpink": "#E095BE",
    "darkpink": "#A84A7A",

    "cyan": "#56A8D8",
    "lightcyan": "#84C3E5",
    "darkcyan": "#3A85B0"
}


class ThemingManager:
    def __init__(self, comm):

        self.comm = comm

        self.comm.register(
            "thememgr",
            {
                "stdcolors": self.get_stdcolors
            }
        )

        self.setup_theming()

    def setup_theming(self):

        palette = QPalette()

        for i in FLUORITE_CS:
            palette.setColor(getattr(QPalette.ColorRole, i), 
                             QColor(FLUORITE_CS[i]))

        QIcon.setThemeName("breeze-dark")

        QApplication.instance().setPalette(palette)
        QApplication.instance().setStyleSheet(STYLESHEET)
        QApplication.instance().setStyle("oxygen")
        QApplication.instance().setFont(QFont("Noto Sans", 10))

    def get_stdcolors(self):

        colors = STD_COLORS
        colors["fg"] = STD_COLORS["white"]
        colors["bg"] = STD_COLORS["black"]
        colors["accent"] = STD_COLORS["blue"]
        colors["transparent"] = "#00000000"

        return colors
