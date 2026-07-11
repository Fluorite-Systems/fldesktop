from pathlib import Path
import json
import logging


class LocaleManager:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register(
            "localemgr", {
                "tr": self.translate,
                "get_kb_locales": self.get_kb_locales
            }
        )

        self.translation = {}
        self.kb_locales = []

        self.setup_locale()

    def setup_locale(self) -> None:
        ui_lang = self.comm.request("cfgmgr", "get", "language")
        
        # Load translation from assets

        tr_path = Path(__file__).resolve().parent \
            / "assets" / "translations" / f"{ui_lang}.json"

        if tr_path.exists():
            with open(tr_path) as f:
                self.translation = json.load(f)
        else:
            logging.warning(f"Translation {ui_lang} does not exists")

    def translate(self, base: str) -> str:
        "Translate base text"
        
        if base in self.translation:
            return self.translation[base]
        
        return base

    def get_kb_locales(self) -> list:
        
        l = self.comm.request("cfgmgr", "get", "kb_locales")

        return l if l else ["en_US"]
