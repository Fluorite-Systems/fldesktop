from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut

from fldesktop.include.compositor.widgets import (
    widget_table, RootWidget, Widget
)
from fldesktop.include.widgets.sidebar import Sidebar, SidebarItem

from typing import Dict, List, Any

import logging

import locale


class Parser:
    def __init__(self, runner):

        self.runner = runner
        self.data = None

    def build(self, data):

        logging.debug(f"Building tree for client {self.runner.uuid}")

        self.data = data
        objects = data.get("layout", {})

        root = RootWidget(self.runner)

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


    def build_tree_from_objects(self, objects: Dict[str, Any], parent = None):
        Objects = []
        for name, cfg in objects.items():
            Objects.append(self.build_object(name, cfg, parent))
        return Objects

    def build_object(self, name: str, cfg: Dict[str, Any], parent = None):
        object_type = cfg.get("type", "unknown")
        # всё, что не type и children, считаем свойствами
        props = {k: v for k, v in cfg.items() if k not in ("type", "children")}
        # obj = Object(self.runner, name, object_type, parent, props)

        if object_type in widget_table:
            obj = widget_table[object_type](self.runner, name, props, parent)
        else:
            obj = Widget(self.runner, name, props, parent)

        if parent:
            parent.children.append(obj)

        children_cfg = cfg.get("children", {})
        obj.children = [
            self.build_object(child_name, child_cfg, obj)
            for child_name, child_cfg in children_cfg.items()
        ]
        return obj

    def print_tree(self, Objects: List, indent: int = 0):
        pad = "  " * indent
        for Object in Objects:
            logging.debug(f"{pad}{Object.name} ({Object.type}) {Object.props}")
            if Object.children:
                self.print_tree(Object.children, indent + 1)
    
    def build_menu(self, data: dict):

        def add_menu_item(parent_menu, key, item):
            if isinstance(item, dict) and "text" in item:
                # Это обычный пункт меню (QAction)
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
            elif isinstance(item, dict):
                # Это подменю (QMenu)
                sub_menu = QMenu(key.replace("_", " ").title())
                parent_menu.addMenu(sub_menu)
                for sub_key, sub_item in item.items():
                    add_menu_item(sub_menu, sub_key, sub_item)

        menu = QMenu()
        for key, item in data.items():
            add_menu_item(menu, key, item)
        
        return menu

    def setup_menu(self):
        if "menu" in self.data:
            menu = self.build_menu(self.data["menu"])
            self.runner.comm.send("wm", "set_window_menu",
                                  (self.runner.winid, menu))
    
    def setup_sidebar(self):

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
            
            self.runner.comm.send("wm", "set_window_sidebar",
                                  self.runner.winid, s)