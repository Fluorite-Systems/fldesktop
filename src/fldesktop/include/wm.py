from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                               QLabel, QToolButton) 
from PySide6.QtCore import Qt, QPoint, QSize, Signal
from PySide6.QtGui import QIcon

from fldesktop.include.widgets.surface import Surface
from fldesktop.include.widgets.animation import Animation

import logging


class Overlay(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, 
                        False)
        self.setObjectName("overlay")
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 50)"
        )
    
    def mousePressEvent(self, event):
        self.parent().mousePressEvent(event)
        
    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().enterEvent(event)


class Window(Surface):
    on_close = Signal()

    def __init__(self, widget: QWidget, name: str, pkgname: str,
                    parent: QWidget, identificator: int,
                    comm, icon: QIcon, size: tuple = (400, 400)
                ) -> None:
        super().__init__(comm, parent)

        self.setObjectName("surface")
        self.setAttribute(Qt.WA_DeleteOnClose)


        self.widget = widget
        self.name = name
        self.pkgname = pkgname
        self.id = identificator
        self.comm = comm
        self.qicon = icon

        self.sidebar = None

        # Focusing overlay
        self.overlay = Overlay(self)
        self.overlay.setObjectName("ov")
        self.overlay.show()
        self.overlay.lower()

        # Setup gui
        self.resize(size[0], size[1])
        self.move(
            (parent.width() - size[0]) // 2,
            (parent.height() - size[1]) // 2
        )
        self.setMouseTracking(True)

        # Layouts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.layout.setSpacing(1)
        self.tlayout = QHBoxLayout() # Title layout
        self.tlayout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.tlayout)

        # Title widgets
        self.icon = QLabel(pixmap = icon.pixmap(QSize(24, 244)))
        self.title = QLabel(self.name)
        self.iconify_btn = QToolButton(
            icon=self.comm.request("iconmgr", "get", "window-minimize")
        )
        self.maximize_btn = QToolButton(
            icon=self.comm.request("iconmgr", "get", "window-maximize")
        )
        self.close_btn = QToolButton(
            icon=self.comm.request("iconmgr", "get", "window-close")
        )
        self.iconify_btn.clicked.connect(self.toggle_minimized)
        self.maximize_btn.clicked.connect(self.toggle_maximized)
        self.close_btn.clicked.connect(self.close_window)

        self.tlayout.addWidget(self.icon)
        self.tlayout.addSpacing(3)
        self.tlayout.addWidget(self.title)

        self.tlayout.addStretch()
        
        for i in [self.iconify_btn, self.maximize_btn, self.close_btn]:
            self.tlayout.addWidget(i)
            i.setObjectName("flatbtn")
            i.setFixedSize(24, 24)

        self.layout.addWidget(self.widget)
        
        self.widget.setMouseTracking(True)

        self.cur_mapping = {
            "l": Qt.CursorShape.SizeHorCursor,
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "t": Qt.CursorShape.SizeVerCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
            "": Qt.CursorShape.ArrowCursor
        }
        self.prev_cur_rd = ""

        # General window management flags
        self.minimized = False
        self.maximized = False
        self.prev_pos_mx = None
        self.prev_size_mx = None
        self.prev_pos_mi = None
        self.prev_size_mi = None

        # Geometry management flags
        self.resizing_allowed = True
        self.resizing = False
        self.dragging = False
        self.resizing_dir = ""
        self.resize_handle_size = 5
        self.resize_start_pos = QPoint(0, 0)
        self.resize_start_size = QSize(600, 400)
        self.drag_start_pos = QPoint(0, 0)
        self.min_size = QSize(100, 100)

        # Show window
        self.animate_open()
    
    def close_window(self) -> None:
        "Closes the window"

        Animation(
            self.comm, self.parent(), self.grab(), "wclose",
            {"pos": self.pos(), "size": self.size()},
            lambda: ...
        )
        self.on_close.emit()
        self.close() 

    def replace_widget(self, new_widget: QWidget) -> None:

        self.layout.removeWidget(self.widget)
        self.layout.addWidget(new_widget)
        new_widget.setMouseTracking(True)
        self.widget = new_widget
   
    def toggle_minimized(self) -> None:
        if not self.minimized:
            self.prev_pos_mi = self.pos()
            self.prev_size_mi = self.size()
            self.animate_minimize()
            self.minimized = True
            self.comm.send(
                "panel", "add_minimized", self.qicon, self.toggle_minimized
            )
            self.comm.send("wm", "change_focus")
        else:
            self.animate_unminimize()
            self.minimized = False
            self.comm.send("wm", "change_focus", self.id)
    
    def toggle_maximized(self) -> None:
        if not self.maximized:
            self.prev_pos_mx = self.pos()
            self.prev_size_mx = self.size()
            self.animate_maximize()
            self.maximize_btn.setIcon(
                self.comm.request("iconmgr", "get", "window-restore")
            )

            self.maximized = True
        else:
            self.animate_unmaximize()

            self.maximize_btn.setIcon(
                self.comm.request("iconmgr", "get", "window-maximize")
            )


            self.maximized = False
        
    def animate_minimize(self) -> None:

        self.hide()
        Animation(
            self.comm, self.parent(), self.grab(), "wminimize",
            {"pos": self.pos(), "size": self.size()},
            lambda: ...
        )

    def animate_maximize(self) -> None:
        
        pos = QPoint(0, 26)
        size = QSize(self.parent().size().width(),
                     self.parent().size().height() - 26)
        self.hide()
        self.resize(size)
        self.move(pos)
        Animation(
            self.comm, self.parent(), self.grab(), "wmaximize",
            {"pos": pos, "size": size},
            self.show
        )

    def animate_unminimize(self) -> None:

        Animation(
            self.comm, self.parent(), self.grab(), "wunminimize",
            {"pos": self.prev_pos_mi, "size": self.prev_size_mi},
            self.show
        )

    
    def animate_unmaximize(self) -> None:
        
        self.hide()
        self.resize(self.prev_size_mx)
        self.move(self.prev_pos_mx)
        Animation(
            self.comm, self.parent(), self.grab(), "wunmaximize",
            {"pos": self.prev_pos_mx, "size": self.prev_size_mx},
            self.show
        )
    
    def animate_open(self) -> None:

        def on_finished(self):
            self.show()
            self.raise_()

        Animation(
            self.comm, self.parent(), self.grab(), "wopen",
            {"pos": self.pos(), "size": self.size()},
            lambda: on_finished(self)
        )

    def get_resizing_dir(self, x, y) -> str:
        w = self.width()
        h = self.height()
        resizing_dir = ""

        if x <= self.resize_handle_size and\
            y <= self.resize_handle_size:
            resizing_dir = "tl"
        elif x <= self.resize_handle_size and\
            y >= h - self.resize_handle_size:
            resizing_dir = "bl"
        elif x >= w - self.resize_handle_size and\
            y <= self.resize_handle_size:
            resizing_dir = "tr"
        elif x >= w - self.resize_handle_size and\
            y >= h - self.resize_handle_size:
            resizing_dir = "br"
        elif x <= self.resize_handle_size:
            resizing_dir = "l"
        elif x >= w - self.resize_handle_size:
            resizing_dir = "r"
        elif y <= self.resize_handle_size:
            resizing_dir = "t"
        elif y >= h - self.resize_handle_size:
            resizing_dir = "b"
        
        return resizing_dir
    
    def mousePressEvent(self, event) -> None:
        self.raise_()
        # Change focus
        if self.comm.request("wm", "get_focus") != self.id:
            self.comm.send("wm", "change_focus", self.id)
            self.comm.send("panel", "raise")
            return
        # Check if the mouse is close to the bottom-right corner for resizing
        if not self.maximized:
            x = event.pos().x()
            y = event.pos().y()
            self.resizing_dir = self.get_resizing_dir(x, y)
            
            if self.resizing_dir and self.resizing_allowed:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_size = self.size()

            else:#if event.pos().y() < self.tlayout.sizeHint().height() + 5:
                self.dragging = True
                # Store the initial position of the mouse relative to the square
                self.drag_start_pos = event.pos()
    
    def mouseMoveEvent(self, event) -> None: # Move window

        if self.resizing_dir:
            rd = self.resizing_dir
        else:
            rd = self.get_resizing_dir(event.pos().x(), event.pos().y())
        
        if rd != self.prev_cur_rd:
            self.setCursor(self.cur_mapping[rd])
            self.prev_cur_rd = rd
        
        if self.resizing:
            # Calculate new width and height based on mouse movement
            
            new_width = self.width()
            new_height = self.height()
            new_x = self.x()
            new_y = self.y()
            
            if "r" in self.resizing_dir:
                new_width = self.resize_start_size.width() + \
                    (event.globalPos().x() - self.resize_start_pos.x())
            if "b" in self.resizing_dir:
                new_height = self.resize_start_size.height() + \
                    (event.globalPos().y() - self.resize_start_pos.y())
            
            if "l" in self.resizing_dir:
                new_x = event.globalPos().x()
                new_width = self.resize_start_size.width() + \
                    (self.resize_start_pos.x() - new_x)
            if "t" in self.resizing_dir:
                new_y = event.globalPos().y()
                new_height = self.resize_start_size.height() + \
                    (self.resize_start_pos.y() - new_y)
            
            if new_width > self.min_size.width() and \
                new_height > self.min_size.height():
                self.move(new_x, new_y)
                self.resize(new_width, new_height)
                
        elif self.dragging:
            # Calculate the new position based on the mouse movement
            delta = event.pos() - self.drag_start_pos
            new_pos = self.pos() + delta
            if new_pos.y() > 26:
                self.move(new_pos)
            else:
                self.move(QPoint(new_pos.x(), 26))
        
    def mouseReleaseEvent(self, event) -> None:
        if self.resizing:
            self.resizing = False
            self.resizing_dir = ""
        elif self.dragging:
            self.dragging = False
        super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        self.overlay.resize(self.size())
        if self.sidebar:
            self.sidebar.refresh(self.size())
        return super().resizeEvent(event)


class WindowManager:
    def __init__(self, comm):

        self.comm = comm
        self.comm.register("wm", {
            "create_window": self.create_window,
            "close_window": self.close_window,
            "change_focus": self.change_focus,
            "get_focus": self.get_focus,
            "set_window_menu": self.set_window_menu,
            "set_window_sidebar": self.set_window_sidebar,
            "append_window_title": self.append_window_title
        })

        self.windows = []
        self.curid = 0

        self.focus = None

    
    def create_window(self, params: dict) -> tuple:
        "Creates an window"
        
        self.curid += 1

        logging.info(f"Creating a window with id {id}")

        if params["icon"].isNull():
            params["icon"] = QIcon.fromTheme("applications-other")
        
        if not "package" in params: params["package"] = "internal"

        win = Window(
            params["widget"], params["name"], params["package"],
            self.comm.request("desktop", "get_instance"),
            self.curid, self.comm, params["icon"]
        )
        self.windows.append(win)

        win.on_close.connect(lambda: self.windows.remove(win))

        if "type" in params:
            if params["type"] == "messagebox":
                win.maximize_btn.hide()
                win.iconify_btn.hide()
                win.resize(300, 200)
                win.resizing_allowed = False

        self.change_focus(win.id)

        return win.id, win.on_close

    def close_window(self, id: int) -> None:
        "Closes a window"

        logging.info(f"Closing window with id {id}")

        for win in self.windows:
            if win.id == id:
                win.close_window()
            
    def change_focus(self, id: int = None) -> None:
        "Change window focus"

        for win in self.windows:
            if win.id == self.focus:
                win.overlay.show()
                win.overlay.raise_()
        
        if id != None:
            self.focus = id

            for win in self.windows:
                if win.id == id:
                    win.raise_()
                    win.overlay.lower()
                    win.overlay.hide()
                
    def get_focus(self) -> int:
        "Get focused window's ID"

        return self.focus
    
    def set_window_menu(self, data: tuple) -> None:

        btn = QToolButton()
        btn.setObjectName("flatbtn")
        btn.setFixedSize(24, 24)
        btn.setIcon(QIcon.fromTheme("application-menu-symbolic"))
        menu = data[1]
        btn.clicked.connect(lambda: menu.exec(btn.mapToGlobal(QPoint(0, btn.height()))))
        
        for win in self.windows:
            if win.id == data[0]:
                if win.tlayout.itemAt(4).widget() != win.iconify_btn:
                    w = win.tlayout.takeAt(4).widget()
                    w.close()
                win.tlayout.insertWidget(4, btn)
    
    def set_window_sidebar(self, winid: int, sidebar) -> None:
        
        for win in self.windows:
            if win.id == winid:
                nw = QWidget()
                nl = QHBoxLayout(nw)
                nl.setContentsMargins(0, 0, 0, 0)
                nl.addWidget(sidebar)
                nl.addWidget(win.widget)
                win.replace_widget(nw)
                win.sidebar = sidebar
                sidebar.refresh(win.size())
    
    def append_window_title(self, id: int, title: str) -> None:

        for win in self.windows:
            if win.id == id:
                if title:
                    win.title.setText(f"{win.name} - {title}")
                else:
                    win.title.setText(win.name)
