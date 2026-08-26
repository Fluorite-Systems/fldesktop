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

FLUORITE_DARK_CS = {
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

FLUORITE_LIGHT_CS = {
    "Window": "#f6f7f8",
    "WindowText": "#1e232a",
    "Base": "#ffffff",
    "AlternateBase": "#eef1f4",
    "ToolTipBase": "#f7f7f7",
    "ToolTipText": "#1e232a",
    "PlaceholderText": "#707d8a",
    "Text": "#1e232a",
    "Button": "#fcfcfc",
    "ButtonText": "#1e232a",
    "BrightText": "#ffffff",
    "Highlight": "#4a86e8",
    "HighlightedText": "#ffffff",
    "Light": "#ffffff",
    "Midlight": "#f6f7f7",
    "Dark": "#888e93",
    "Mid": "#c4c8cc",
    "Shadow": "#474a4c",
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

COLORSCHEMES = {
    "dark": (FLUORITE_DARK_CS, "breeze-dark"),
    "neutral": (FLUORITE_DARK_CS, "breeze-dark"),
    "light": (FLUORITE_LIGHT_CS, "breeze-light")
}

SURFACE_PRESETS = {
    "neutral": {
        "base_color": (0, 0, 0),
        "base_alpha": 0
    },
    "dark": {
        "base_color": (0, 0, 0),
        "base_alpha": 100
    },
    "light": {
        "base_color": (255, 255, 255),
        "base_alpha": 100
    }
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
        
        self.comm.subscribe("reload_config", self.setup_theme)

        QApplication.instance().setStyle("oxygen")

        QApplication.instance().setFont(QFont("Noto Sans", 10))

        self.setup_theme()

    def setup_theme(self):
        
        theme = self.comm.request("cfgmgr", "get", "theme")

        cs = COLORSCHEMES[theme] if theme in COLORSCHEMES \
          else COLORSCHEMES["neutral"]

        palette = QPalette()

        for i in cs[0]:
            palette.setColor(getattr(QPalette.ColorRole, i), 
                             QColor(cs[0][i]))

        QApplication.instance().setPalette(palette)

        QIcon.setThemeName(cs[1])

        QApplication.instance().setStyleSheet(STYLESHEET)

    def get_stdcolors(self):

        theme = self.comm.request("cfgmgr", "get", "theme")

        cs = COLORSCHEMES[theme] if theme in COLORSCHEMES \
          else COLORSCHEMES["neutral"]

        colors = STD_COLORS
        colors["fg"] = cs[0]["Text"]
        colors["bg"] = cs[0]["Base"]
        colors["accent"] = STD_COLORS["blue"]
        colors["transparent"] = "#00000000"

        return colors
