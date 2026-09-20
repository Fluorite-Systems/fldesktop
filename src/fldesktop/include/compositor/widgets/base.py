from PySide6.QtCore import Qt

import logging
import locale


class Widget:
    def __init__(self, runner, name, props={}, parent=None):
        self._runner = runner
        self.name = name
        self.props = props
        self.parent = parent
        self.type = "widget"

        self.callables = {}
        self.base_props = {}

    def _cleanup(self):
        ...

    def _setup(self):
        #self._setup_layouting()
        self._runner.widgets[self.name] = self
        
        if hasattr(self, "qwidget"):
            self.callables.update(
                {
                    "show": self.qwidget.show,
                    "hide": self.qwidget.hide
                }
            )
            self.base_props.update(
                {
                    "width": None,
                    "height": None,
                    "drag_enabled": False,
                    "drag_data": "",
                    "drag_mime_type": "",
                    "drop_enabled": False,
                    "drop_mime_types": []
                }
            )

            self.qwidget.setProperty(
                "drop_callback", lambda data, mime: self._runner.event(
                    name=self.name, type="data_dropped",
                    data=data, mimetype=mime
                )
            )

        self.props = {**self.base_props, **self.props}

        self._setup_setters()
        self.apply_props()

    def _setup_layouting(self):
        "Setups widget"

        logging.debug(
            f"Building {self.type} {self.name}; parent is {self.parent.name}"\
                if self.parent else f"Building {self.type} {self.name}"
        )

        if self.parent:
            if self.parent.type in ["app", "vlayout", "hlayout",
                                    "flayout", "container"]:
                if hasattr(self, "qwidget"):
                    self.parent.qlayout.addWidget(self.qwidget)
                elif hasattr(self, "qlayout"):
                    self.parent.qlayout.addLayout(self.qlayout)
                else:
                    self.parent.qlayout.addStretch()
            else:
                if hasattr(self, "qwidget"):
                    self.qwidget.setParent(self.parent.qwidget)
                else:
                    self.parent.qwidget.setLayout(self.qlayout)

        if hasattr(self, "qwidget"):
            if "width" in self.props:
                if type(self.props["width"]) == int:
                    self.qwidget.setFixedWidth(self.props["width"])
            if "height" in self.props:
                if type(self.props["height"]) == int:
                    self.qwidget.setFixedHeight(self.props["height"])
            #self.qwidget.installEventFilter(self._runner.drag_filter)
            #self.qwidget.installEventFilter(self._runner.drop_filter)

    def _setup_setters(self):
        for prop in self.base_props:

            def make_setter(name):
                def setter(**kwargs):
                    if name in kwargs:
                        self.props[name] = kwargs[name]
                        logging.debug(
                            f"Setting {name}={kwargs[name]} to {self.name}"
                        )
                        self.apply_props()

                return setter

            setter = make_setter(prop)
            setattr(self, f"set_{prop}", setter)
            self.callables[f"set_{prop}"] = setter

    def apply_props(self):

        if hasattr(self, "qwidget"):
            if self.props["width"]:
                self.qwidget.setFixedWidth(int(self.props["width"]))
            if self.props["height"]:
                self.qwidget.setFixedHeight(int(self.props["height"]))

            if self.props["drag_enabled"]:
                self.qwidget.setProperty(
                    "drag_enabled", bool(self.props["drag_enabled"])
                )
            if self.props["drag_data"]:
                self.qwidget.setProperty("drag_data", self.props["drag_data"])
            if self.props["drag_mime_type"]:
                self.qwidget.setProperty(
                    "drag_mime_type", self.props["drag_mime_type"]
                )

            if self.props["drop_enabled"]:
                self.qwidget.setAcceptDrops(bool(self.props["drop_enabled"]))
                self.qwidget.setProperty(
                    "drop_enabled", bool(self.props["drop_enabled"])
                )
            if self.props["drop_mime_types"]:
                self.qwidget.setProperty(
                    "drop_mime_types", self.props["drop_mime_types"]
                )
                
            if "menu" in self.props:
                menu = self._runner.parser.build_menu(self.props["menu"])
                self.qwidget.setContextMenuPolicy(Qt.CustomContextMenu)
                self.qwidget.customContextMenuRequested.connect(
                    lambda p: menu.exec(self.qwidget.mapToGlobal(p))
                )

    def delete_bk(self):
        logging.debug(f"Deleting {self.type} {self.name}")

        if self.parent:
            self.parent.children.remove(self)
            if hasattr(self.parent, "qlayout"):
                if hasattr(self, "qwidget"):
                    self.parent.qlayout.removeWidget(self.qwidget)
                    self.qwidget.close()
                    self.qwidget.deleteLater()
                if hasattr(self, "qlayout"):
                    i = self.parent.qlayout.indexOf(self.qlayout)
                    if i != -1:
                        self.parent.qlayout.takeAt(i)

        self._cleanup()

        if hasattr(self, "qwidget"):
            self.qwidget.setParent(None)
            self.qwidget.deleteLater()
        if hasattr(self, "qlayout"):
            self.qlayout.deleteLater()

        self._runner.deleted_widgets.append(self.name)
        self._runner.widgets.pop(self.name)

    def tr(self, base_text: str):
        "Translate text"
        loc = locale.getlocale()[0]

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