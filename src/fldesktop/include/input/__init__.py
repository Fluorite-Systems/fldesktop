from PySide6.QtGui import QInputMethod
from PySide6.QtCore import QLocale


class InputManager:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register(
            "inputmgr", {
                "set_locale": self.set_locale,
                "cycle_locale": self.cycle_locale
            }
        )

        self.load_locales()

    def load_locales(self):
        "Load keyboard locales"

        self.locales = self.comm.request("localemgr", "get_kb_locales")

    def set_locale(self, locale: str) -> None:
        "Set keyboard locale"

        qlocale = QLocale(locale)
        QInputMethod().setLocale(qlocale)

    def cycle_locale(self) -> str:
        "Cycle keyboard locales"
        

