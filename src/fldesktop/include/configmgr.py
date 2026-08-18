from PySide6.QtCore import QFileSystemWatcher
import json


FALLBACK_CONFIG = {
    "background-type": "wallpaper",
    "background-color": "#257565",
    "wallpaper": "/usr/share/wallpapers/Pine Path.jpg",
    "theme": "dark",
    "language": "en_US",
    "kb_locales": ["us"],
    "auth-type": "passwordless",
    "auth-pwhash": ""
}


class ConfigurationManager:
    def __init__(self, comm):
        self.comm = comm
        self.comm.register(
            "cfgmgr", {
                "get": self.get_value,
                "reload": self.load_config
            }
        )

        self.path = self.comm.request(
            "osmgr", "get_path", "flcfg.json"
        )

        self.load_config()

        self.watcher = QFileSystemWatcher([self.path])
        self.watcher.fileChanged.connect(self.on_config_changed)
    
    def load_config(self):
        "Load configuration"

        if self.path:
            with open(self.path) as f:
                try:
                    self.config = json.load(f)
                except json.decoder.JSONDecodeError:
                    self.config = FALLBACK_CONFIG
        else:
            self.config = FALLBACK_CONFIG
    
    def get_value(self, key: str):
        "Return value"

        if key in self.config:
            return self.config[key]
        else:
            if key in FALLBACK_CONFIG:
                return FALLBACK_CONFIG[key]
            else:
                return None
    
    def on_config_changed(self, _):
        "Handle config file changes"

        self.load_config()
        self.comm.emit("reload_config")
