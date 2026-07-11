from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLocale

from fldesktop.include.input.evfilter import InputEventFilter


class InputManager:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register(
            "inputmgr", {
                "set_locale": self.set_locale,
                "cycle_locale": self.cycle_locale,
                "get_current_locale": self.get_current_locale
            }
        )

        self.load_locales()

        self.current_locale = self.locales[0]

        self.filter = InputEventFilter() 
        QApplication.instance().installEventFilter(self.filter)

    def load_locales(self):
        "Load keyboard locales"

        self.locales = self.comm.request("localemgr", "get_kb_locales")

    def set_locale(self, locale: str) -> None:
        "Set keyboard locale"

        self.filter.set_layout(locale)
        self.current_locale = locale

    def cycle_locale(self) -> str:
        "Cycle keyboard locales"

        i = self.locales.index(self.current_locale)

        if i + 1 < len(self.locales):
            self.set_locale(self.locales[i + 1])
            return self.locales[i + 1]
        else:
            self.set_locale(self.locales[0])
            return self.locales[0]

    def get_current_locale(self) -> str:
        "Return the current locale"

        return self.current_locale
