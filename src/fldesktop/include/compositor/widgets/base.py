from PySide6.QtCore import Qt

import logging
import locale


class Widget:
    def __init__(self, runner, name, props, parent):
        self._runner = runner
        self.name = name
        self.props = props
        self.parent = parent
        self.type = "widget"
        self.children = []

        self.callables = {}
        self.base_props = {}

    def _setup(self):
        self._setup_layouting()
        self._runner.widgets[self.name] = self
        
        if hasattr(self, "qwidget"):
            self.callables.update(
                {
                    "show": self.qwidget.show,
                    "hide": self.qwidget.hide,
                    "set_width": lambda width: \
                        self.qwidget.setFixedWidth(int(width)),
                    "set_height": lambda height: \
                        self.qwidget.setFixedHeight(int(height))
                }
            )
            self.base_props.update(
                {
                    "width": None,
                    "height": None
                }
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
            if "menu" in self.props:
                menu = self._runner.parser.build_menu(self.props["menu"])
                self.qwidget.setContextMenuPolicy(Qt.CustomContextMenu)
                self.qwidget.customContextMenuRequested.connect(
                    lambda p: menu.exec(self.qwidget.mapToGlobal(p))
                )

    def _setup_setters(self):
        for prop in self.base_props:

            def make_setter(f_name):
                def setter(**kwargs):
                    if f_name in kwargs:
                        self.props[f_name] = kwargs[f_name]
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
                self.qwidget.setFixedWidth(int(self.props["height"]))

    def update_children(self, tree: dict):

        for i in self.children:
            i.delete()

        # Теперь строим новое дерево
        self._runner.parser.build_tree_from_objects(tree, self)

    def clear_children(self):

        for i in self.children:
            i.delete()

    def add_child(self, name: str, props: dict):

        self._runner.parser.build_tree_from_objects({
            name: props
        }, self)

    def delete(self):
        logging.debug(f"Deleting {self.type} {self.name}")
        logging.debug(f"{self.name} has {self.children} at the moment of its death")
        for i in self.children[:]:
            logging.debug(f"{self.name} deletes {i.name}!")
            i.delete()

        if self.parent:
            self.parent.children.remove(self)
            if hasattr(self.parent, "qlayout"):
                if hasattr(self, "qwidget"):
                    self.parent.qlayout.removeWidget(self.qwidget)
                if hasattr(self, "qlayout"):
                    i = self.parent.qlayout.indexOf(self.qlayout)
                    if i != -1:
                        self.parent.qlayout.takeAt(i)

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
