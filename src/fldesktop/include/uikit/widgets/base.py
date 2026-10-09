from PySide6.QtCore import Qt

from fldesktop.include.uikit.ui import UI

import logging
import locale


BASEATTRS = {
    "width": None,
    "height": None,
    "drag_enabled": False,
    "drag_data": "",
    "drag_mime_type": "",
    "drop_enabled": False,
    "drop_mime_types": []
}


class Widget(UI):
    def __init__(self, comm, name, attrs={}, baseattrs={}):
        baseattrs.update(BASEATTRS)
        super().__init__(comm, name, attrs, baseattrs)
        self.type = "widget"

        self.callables = {}

    def _cleanup(self):
        ...

    def _setup(self):
        #self._setup_layouting()
        
        if hasattr(self, "qwidget"):
            self.callables.update(
                {
                    "show": self.qwidget.show,
                    "hide": self.qwidget.hide
                }
            )
            self.baseattrs.update(
                
            )

            self.qwidget.setProperty(
                "drop_callback", lambda data, mime: self.event(
                    type="data_dropped",
                    data=data, mimetype=mime
                )
            )

        self.attrs = {**self.baseattrs, **self.attrs}

        self._setup_setters()
        self.apply_attrs()

        #self.qwidget.installEventFilter(self._runner.drag_filter)
        #self.qwidget.installEventFilter(self._runner.drop_filter)

    def _setup_setters(self):
        for prop in self.baseattrs:

            def make_setter(name):
                def setter(**kwargs):
                    if name in kwargs:
                        self.attrs[name] = kwargs[name]
                        logging.debug(
                            f"Setting {name}={kwargs[name]} to {self.name}"
                        )
                        self.apply_attrs()

                return setter

            setter = make_setter(prop)
            setattr(self, f"set_{prop}", setter)
            self.callables[f"set_{prop}"] = setter

    def apply_attrs(self):
        super().apply_attrs()

        if hasattr(self, "qwidget"):
            if self.attrs["width"]:
                self.qwidget.setFixedWidth(int(self.attrs["width"]))
            if self.attrs["height"]:
                self.qwidget.setFixedHeight(int(self.attrs["height"]))

            if self.attrs["drag_enabled"]:
                self.qwidget.setProperty(
                    "drag_enabled", bool(self.attrs["drag_enabled"])
                )
            if self.attrs["drag_data"]:
                self.qwidget.setProperty("drag_data", self.attrs["drag_data"])
            if self.attrs["drag_mime_type"]:
                self.qwidget.setProperty(
                    "drag_mime_type", self.attrs["drag_mime_type"]
                )

            if self.attrs["drop_enabled"]:
                self.qwidget.setAcceptDrops(bool(self.attrs["drop_enabled"]))
                self.qwidget.setProperty(
                    "drop_enabled", bool(self.attrs["drop_enabled"])
                )
            if self.attrs["drop_mime_types"]:
                self.qwidget.setProperty(
                    "drop_mime_types", self.attrs["drop_mime_types"]
                )
                
            if "menu" in self.attrs:
                menu = self._runner.parser.build_menu(self.attrs["menu"])
                self.qwidget.setContextMenuPolicy(Qt.CustomContextMenu)
                self.qwidget.customContextMenuRequested.connect(
                    lambda p: menu.exec(self.qwidget.mapToGlobal(p))
                )

    def delete(self):
        logging.debug(f"Deleting {self.type} {self.name}")

        self._cleanup()

        if hasattr(self, "qwidget"):
            self.qwidget.setParent(None)
            self.qwidget.deleteLater()
        if hasattr(self, "qlayout"):
            self.qlayout.deleteLater()

    def tr(self, base_text: str):
        "Translate text"
        loc = locale.getlocale()[0]

        return base_text

        if loc in self._runner.translations:
            trs = self._runner.translations[loc]
            if base_text in trs:
                return trs[base_text]

        return base_text


    def reparent(self, parent):

        logging.debug(f"Reparenting {self} to {parent}")

        if hasattr(parent, "qlayout"):
            if hasattr(self, "qlayout"):
                parent.qlayout.addLayout(self.qlayout)
                logging.debug(f"Added {self}'s layout to {parent}'s one")
            elif hasattr(self, "qwidget"):
                parent.qlayout.addWidget(self.qwidget)
                logging.debug(f"Added {self}'s widget to {parent}'s layout")

        self.parent = parent

    def set_index(self, index: int):

        ...