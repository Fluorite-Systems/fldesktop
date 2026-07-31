from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut

from fldesktop.include.compositor.widgets import widgets
from fldesktop.include.compositor.widgets.base import Widget
from fldesktop.include.widgets.sidebar import Sidebar, SidebarItem

import logging
import locale


class Parser:
    def __init__(self, runner) -> None:

        self.runner = runner
        self.data = None

    def build(self, data: dict):
        "Build widget tree from layout"

        logging.debug(f"Building tree for client {self.runner.uuid}")

        self.data = data
        objects = data.get("layout", {})

        root = widgets["root"](self.runner)

        root.children = self.build_tree_from_objects(objects, parent=root)

        self.print_tree([root])

        if "keybinds" in self.data:
            for k in self.data["keybinds"]:
                QShortcut(QKeySequence(k), self.runner.widget)\
                    .activated.connect(
                        lambda: self.runner.runtime.exec(
                            self.data["keybinds"][k]
                        )
                    )

        self.setup_menu()
        self.setup_sidebar()

        return root


    def build_tree_from_objects(self, objects: dict, parent = None) -> list:
        "Build widget tree from objects dict"

        Objects = []
        for name, cfg in objects.items():
            Objects.append(self.build_object(name, cfg, parent))
        return Objects

    def build_object(self, name: str, cfg: dict, parent = None) -> Widget:
        "Build widget object"

        if not name in self.runner.widgets:
            object_type = cfg.get("type", "unknown")
            props = {k: v for k, v in cfg.items() if k not in ("type", "children")}

            if object_type in widgets:
                obj = widgets[object_type](self.runner, name, props, parent)
            else:
                obj = Widget(self.runner, name, props, parent)

            if parent:
                parent.children.append(obj)

        else:
            obj = self.runner.widgets[name]

        children_cfg = cfg.get("children", {})
        obj.children = [
            self.build_object(child_name, child_cfg, obj)
            for child_name, child_cfg in children_cfg.items()
        ]
        return obj

    def print_tree(self, Objects: list, indent: int = 0) -> None:
        "Print object tree"

        pad = "  " * indent
        for Object in Objects:
            logging.debug(f"{pad}{Object.name} ({Object.type}) {Object.props}")
            if Object.children:
                self.print_tree(Object.children, indent + 1)
    
    def build_menu(self, data: dict) -> QMenu:
        "Build a QMenu from json layout"

        def add_menu_item(parent_menu, key, item):
            if isinstance(item, dict) and "children" in item \
                and "text" in item:
                # Submenu
                trs = self.runner.translations
                loc = locale.getlocale()[0]
                if loc in trs:
                    if item["text"] in trs[loc]:
                        item["text"] = trs[loc][item["text"]]

                sub_menu = QMenu(item["text"])
                parent_menu.addMenu(sub_menu)
                for sub_key, sub_item in item["children"].items():
                    add_menu_item(sub_menu, sub_key, sub_item)

            elif isinstance(item, dict) and "text" in item:
                # Menu item
                trs = self.runner.translations
                loc = locale.getlocale()[0]
                if loc in trs:
                    if item["text"] in trs[loc]:
                        item["text"] = trs[loc][item["text"]]
                action = QAction(item["text"], self.runner.widget)
                if "icon" in item:
                    icon = QIcon.fromTheme(item["icon"])
                    if not icon.isNull():
                        action.setIcon(icon)
                action.triggered.connect(
                    lambda: self.runner.event(type="action_press", name=key)
                )
                parent_menu.addAction(action)

        menu = QMenu()
        for key, item in data.items():
            add_menu_item(menu, key, item)
        
        return menu

    def setup_menu(self) -> None:
        "Setup QMenu"

        if "menu" in self.data:
            menu = self.build_menu(self.data["menu"])
            self.runner.comm.request("wm", "set_window_menu",
                                  (self.runner.winid, menu))
    
    def setup_sidebar(self) -> None:
        "Setup sidebar thingie"

        if "sidebar" in self.data:
            s = Sidebar()

            for name, props in self.data["sidebar"].items():
                i = SidebarItem()
                
                if "text" in props:
                    i.setText(props["text"])
                else:
                    i.setText(name)
                
                if "icon" in props:
                    ico = QIcon.fromTheme(props["icon"])
                    i.setIcon(ico)

                i.clicked.connect(
                    lambda _, n=name: self.runner.event(
                        type="sidebar_button_press",
                        name=n
                    )
                )
                
                s.add_item(i)
            
            self.runner.comm.request("wm", "set_window_sidebar",
                                  self.runner.winid, s)
