from __future__ import annotations

from typing import Optional

from PySide6.QtCore import (
    Qt, QPoint, QTimer, QEvent, QObject, Signal, QEventLoop
)
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QPushButton, QSizePolicy
)

from fldesktop.include.widgets.surface import Surface

_MENU_QSS = """
#menuRoot QPushButton {
    text-align: left;
    padding: 4px 22px 4px 22px;
    min-height: 20px;
}

#menuRoot QPushButton[separator="true"] {
    padding: 0px;
    margin: 4px 6px;
    min-height: 1px;
    max-height: 1px;
}
"""


class _MenuItemButton(QPushButton):

    hovered = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFlat(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setIconSize(self.iconSize())

    def enterEvent(self, event):
        self.hovered.emit()
        super().enterEvent(event)


class Menu(Surface):

    aboutToShow = Signal()
    aboutToHide = Signal()
    triggered = Signal(QAction)
    hovered = Signal(QAction)

    def __init__(self, comm, parent: Optional[QWidget] = None, title: str = ""):
        super().__init__(comm, 2)
        self._title = title
        self._actions: list[QAction] = []
        self._buttons: list[_MenuItemButton] = []
        self._submenus: dict[QAction, "Menu"] = {}
        self._active_submenu: Optional["Menu"] = None
        self._filter_installed = False
        self._app: Optional[QApplication] = None
        self._exec_loop: Optional[QEventLoop] = None
        self._exec_result: Optional[QAction] = None
        self._exec_pending = False

        self._submenu_timer = QTimer(self)
        self._submenu_timer.setSingleShot(True)
        self._submenu_timer.setInterval(200)
        self._submenu_timer.timeout.connect(self._open_pending_submenu)
        self._pending_submenu_action: Optional[QAction] = None

        self.setObjectName("menuRoot")
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(_MENU_QSS)
        self.hide()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def _install_filter(self):
        if self._filter_installed:
            return
        app = QApplication.instance()
        if app is None:
            return
        self._app = app
        app.installEventFilter(self)
        self._filter_installed = True

    def _remove_filter(self):
        if not self._filter_installed:
            return
        if self._app is not None:
            self._app.removeEventFilter(self)
        self._filter_installed = False
        self._app = None

    def closeEvent(self, event):
        self._remove_filter()
        self._submenu_timer.stop()
        super().closeEvent(event)

    def addAction(self, action_or_text, *args, **kwargs) -> QAction:
        if isinstance(action_or_text, QAction):
            action = action_or_text
        elif isinstance(action_or_text, str):
            action = QAction(action_or_text, self)
            if args and callable(args[0]):
                action.triggered.connect(args[0])
        else:
            icon = action_or_text
            text = args[0] if args else ""
            action = QAction(icon, text, self)
            if len(args) > 1 and callable(args[1]):
                action.triggered.connect(args[1])
            elif kwargs.get("triggered"):
                action.triggered.connect(kwargs["triggered"])
        self._append_action(action)
        return action

    def addMenu(self, menu_or_title, *args) -> "Menu":
        if isinstance(menu_or_title, Menu):
            submenu = menu_or_title
            title = submenu._title
        else:
            title = menu_or_title
            submenu = Menu(self, title)
        action = QAction(title, self)
        action.setMenu(submenu)
        self._append_action(action)
        self._submenus[action] = submenu
        return submenu

    def addSeparator(self):
        action = QAction(self)
        action.setSeparator(True)
        self._append_action(action)

    def insertAction(self, before: QAction, action: QAction) -> QAction:
        idx = self._actions.index(before) if before in self._actions else len(self._actions)
        self._actions.insert(idx, action)
        self._rebuild()
        return action

    def insertSeparator(self, before: QAction):
        action = QAction(self)
        action.setSeparator(True)
        self.insertAction(before, action)

    def removeAction(self, action: QAction):
        if action not in self._actions:
            return
        self._actions.remove(action)
        self._submenus.pop(action, None)
        self._rebuild()

    def clear(self):
        self._actions.clear()
        self._submenus.clear()
        self._rebuild()

    def actions(self) -> list[QAction]:
        return list(self._actions)

    def isEmpty(self) -> bool:
        return not any(not a.isSeparator() for a in self._actions)

    def title(self) -> str:
        return self._title

    def setTitle(self, title: str):
        self._title = title

    def exec(self, global_pos: QPoint) -> Optional[QAction]:
        if self._exec_pending or self._exec_loop is not None:
            return None
        self._exec_pending = True
        QTimer.singleShot(0, lambda: self._exec_deferred(global_pos))
        return None

    def _exec_deferred(self, global_pos: QPoint):
        self._exec_pending = False
        if self._exec_loop is not None:
            return
        self._exec_result = None
        self._exec_loop = QEventLoop(self)

        def on_triggered(action: QAction):
            self._exec_result = action
            if self._exec_loop is not None:
                self._exec_loop.quit()

        def on_hidden():
            if self._exec_loop is not None:
                self._exec_loop.quit()

        self.triggered.connect(on_triggered)
        self.aboutToHide.connect(on_hidden)
        self.popup(global_pos)
        self._exec_loop.exec()

        try:
            self.triggered.disconnect(on_triggered)
        except (RuntimeError, TypeError):
            pass
        try:
            self.aboutToHide.disconnect(on_hidden)
        except (RuntimeError, TypeError):
            pass

        self._exec_loop = None

    def popup(self, global_pos: QPoint):
        parent = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()
        local_pos = parent.mapFromGlobal(global_pos)
        screen = parent.screen().availableGeometry() if parent.screen() else None
        if screen is not None:
            if local_pos.y() + self.height() > screen.bottom():
                local_pos.setY(max(screen.top(), local_pos.y() - self.height()))
            if local_pos.x() + self.width() > screen.right():
                local_pos.setX(max(screen.left(), local_pos.x() - self.width()))
        self.move(local_pos)
        self._install_filter()
        self.show()
        self.raise_()
        self.aboutToShow.emit()

    def showEvent(self, event):
        self._install_filter()
        super().showEvent(event)

    def hideEvent(self, event):
        self._submenu_timer.stop()
        self._pending_submenu_action = None
        self._close_all_submenus()
        self._remove_filter()
        self.aboutToHide.emit()
        super().hideEvent(event)

    def _append_action(self, action: QAction):
        self._actions.append(action)
        self._rebuild()
        if isinstance(action.menu(), Menu):
            self._submenus[action] = action.menu()

    def _compose_text(self, action: QAction) -> str:
        text = action.text()
        if action.shortcut():
            shortcut = action.shortcut().toString(QKeySequence.NativeText)
            text = text + "\u2003\u2003" + shortcut
        if action.menu():
            text = text + "  \u25b6"
        return text

    def _ensure_pool(self, n: int):
        while len(self._buttons) < n:
            idx = len(self._buttons)
            btn = _MenuItemButton(self)
            btn.clicked.connect(self._make_click_handler(idx))
            btn.hovered.connect(self._make_hover_handler(idx))
            self._layout.addWidget(btn)
            self._buttons.append(btn)

    def _make_click_handler(self, idx: int):
        def handler():
            self._on_button_clicked(idx)
        return handler

    def _make_hover_handler(self, idx: int):
        def handler():
            self._on_button_hovered(idx)
        return handler

    def _on_button_clicked(self, idx: int):
        if idx < 0 or idx >= len(self._actions):
            return
        action = self._actions[idx]
        if action.isSeparator():
            return
        if action.menu() is not None:
            self._open_submenu(action)
            return
        action.trigger()
        self.triggered.emit(action)
        self._close_whole_tree()

    def _on_button_hovered(self, idx: int):
        if idx < 0 or idx >= len(self._actions):
            return
        action = self._actions[idx]
        if action.isSeparator():
            return
        self.hovered.emit(action)
        if action.menu() is not None:
            self._pending_submenu_action = action
            self._submenu_timer.start()
        else:
            self._submenu_timer.stop()
            self._pending_submenu_action = None
            if self._active_submenu is not None:
                self._close_active_submenu()

    def _rebuild(self):
        n = len(self._actions)
        self._ensure_pool(n)

        for i, action in enumerate(self._actions):
            btn = self._buttons[i]
            self._configure_button(btn, action)
            btn.setVisible(True)

        for i in range(n, len(self._buttons)):
            self._buttons[i].setVisible(False)

        self.adjustSize()

    def _configure_button(self, btn: _MenuItemButton, action: QAction):
        if action.isSeparator():
            btn.setProperty("separator", True)
            btn.setText("")
            btn.setIcon(QIcon())
            btn.setEnabled(True)
        else:
            btn.setProperty("separator", False)
            btn.setText(self._compose_text(action))
            btn.setIcon(action.icon())
            btn.setEnabled(action.isEnabled())

        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()

    def _open_pending_submenu(self):
        if self._pending_submenu_action is not None:
            self._open_submenu(self._pending_submenu_action)

    def _open_submenu(self, action: QAction):
        submenu = self._submenus.get(action)
        if submenu is None:
            return
        if self._active_submenu is not None and self._active_submenu is not submenu:
            self._close_active_submenu()

        idx = self._actions.index(action) if action in self._actions else -1
        if idx < 0 or idx >= len(self._buttons):
            return

        item = self._buttons[idx]
        parent = self.parentWidget()
        if parent is None:
            return

        submenu.adjustSize()
        item_pos = item.mapTo(parent, QPoint(item.width(), 0))
        screen = parent.screen().availableGeometry() if parent.screen() else None
        if screen is not None:
            if item_pos.x() + submenu.width() > screen.right():
                item_pos.setX(
                    max(screen.left(),
                        item_pos.x() - item.width() - submenu.width())
                )
            if item_pos.y() + submenu.height() > screen.bottom():
                item_pos.setY(
                    max(screen.top(), screen.bottom() - submenu.height())
                )

        submenu.setParent(parent)
        submenu.move(item_pos)
        submenu.show()
        submenu.raise_()
        submenu.aboutToShow.emit()
        self._active_submenu = submenu

    def _close_active_submenu(self):
        if self._active_submenu is not None:
            self._active_submenu.hide()
            self._active_submenu = None

    def _close_all_submenus(self):
        for submenu in self._submenus.values():
            submenu._close_all_submenus()
            submenu.hide()
        self._active_submenu = None

    def _close_whole_tree(self):
        self._close_all_submenus()
        self.hide()
        parent = self.parentWidget()
        while parent is not None:
            if isinstance(parent, Menu):
                parent._close_all_submenus()
                parent.hide()
            parent = parent.parentWidget()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if not self.isVisible():
            return super().eventFilter(obj, event)
        if event.type() == QEvent.MouseButtonPress:
            pos = event.globalPosition().toPoint()
            if not self._contains_global(pos):
                self._close_whole_tree()
        return super().eventFilter(obj, event)

    def _contains_global(self, global_pos: QPoint) -> bool:
        if not self.isVisible():
            return False
        if self.rect().contains(self.mapFromGlobal(global_pos)):
            return True
        for submenu in self._submenus.values():
            if submenu._contains_global(global_pos):
                return True
        return False