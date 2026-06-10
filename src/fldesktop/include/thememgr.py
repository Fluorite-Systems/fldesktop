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

              QPushButton#flatbtn
              {
                border: 1;
                border-radius: 13;
                background-color: rgba(0, 0, 0, 0);
              }

              QPushButton#flatbtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
              }

              QPushButton#flatbtn::pressed
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

BREEZE_DARK_CS = {
    "Window": "#2a2e32",
    "WindowText": "#fcfcfc",
    "Base": "#1b1e20",
    "AlternateBase": "#232629",
    "ToolTipBase": "#31363b",
    "ToolTipText": "#fcfcfc",
    "PlaceholderText": "#a1a9b1",
    "Text": "#fcfcfc",
    "Button": "#31363b",
    "ButtonText": "#fcfcfc",
    "BrightText": "#ffffff",
    "Highlight": "#3daee9",
    "HighlightedText": "#fcfcfc",
    "Light": "#474d54",
    "Midlight": "#3a4045",
    "Dark": "#141618",
    "Mid": "#24282b",
    "Shadow": "#0f1012"
}

BREEZE_LIGHT_CS = {
    "Window": "#eff0f1",
    "WindowText": "#232629",
    "Base": "#ffffff",
    "AlternateBase": "#f7f7f7",
    "ToolTipBase": "#f7f7f7",
    "ToolTipText": "#232629",
    "PlaceholderText": "#707d8a",
    "Text": "#232629",
    "Button": "#fcfcfc",
    "ButtonText": "#232629",
    "BrightText": "#ffffff",
    "Highlight": "#3daee9",
    "HighlightedText": "#ffffff",
    "Light": "#ffffff",
    "Midlight": "#f6f7f7",
    "Dark": "#888e93",
    "Mid": "#c4c8cc",
    "Shadow": "#474a4c",
    "Link": "#2980b9",
    "LinkVisited": "#9b59b6"
}

COLORSCHEMES = {
    "dark": (BREEZE_DARK_CS, "breeze-dark"),
    "light": (BREEZE_LIGHT_CS, "breeze-light"),
    "neutral": (BREEZE_DARK_CS, "breeze-dark")
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