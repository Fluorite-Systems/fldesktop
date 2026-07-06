from PySide6.QtGui import QPalette, QColor, QIcon, QFont

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

              QWidget#traybtn
              {
                background-color: transparent;
              }

              QWidget#traybtn::hover
              {
                background-color: rgba(255, 255, 255, 150);
                border-radius: 1;
              }

              QWidget#traybtn::pressed
              {
                background-color: #00d2ff
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
    "red": "#D95C5C",
    "orange": "#E89A4A",
    "yellow": "#E0B84D",
    "green": "#43B77A",
    "teal": "#5AA7A2",
    "blue": "#4A86E8",
    "indigo": "#6673C6",
    "purple": "#9575CD",
    "pink": "#CB6A9E",
    "cyan": "#56A8D8"
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
    def __init__(self, app, comm):
        self.app = app
        self.comm = comm

        self.comm.register(
            "thememgr",
            {
                "stdcolors": self.get_stdcolors
            }
        )
        
        self.comm.subscribe("reload_config", self.setup_theme)

        app.setStyle("oxygen")

        app.setFont(QFont("Noto Sans", 10))

        self.setup_theme()

    def setup_theme(self):
        
        theme = self.comm.request("cfgmgr", "get", "theme")

        cs = COLORSCHEMES[theme] if theme in COLORSCHEMES \
          else COLORSCHEMES["neutral"]

        palette = QPalette()

        for i in cs[0]:
            palette.setColor(getattr(QPalette.ColorRole, i), 
                             QColor(cs[0][i]))

        self.app.setPalette(palette)

        QIcon.setThemeName(cs[1])

        self.app.setStyleSheet(STYLESHEET)

    def get_stdcolors(self):

        theme = self.comm.request("cfgmgr", "get", "theme")

        cs = COLORSCHEMES[theme] if theme in COLORSCHEMES \
          else COLORSCHEMES["neutral"]

        colors = STD_COLORS
        colors["fg"] = cs[0]["Text"]
        colors["bg"] = cs[0]["Base"]
        colors["accent"] = STD_COLORS["blue"]

        return colors
