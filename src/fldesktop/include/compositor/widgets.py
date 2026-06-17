from PySide6.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout,
                               QLabel, QPushButton, QLineEdit,
                               QTextEdit, QTabWidget, QScrollArea,
                               QSlider, QCheckBox, QRadioButton)
from PySide6.QtGui import (QIcon, QPainter, QPainterPath,
                           QPixmap, QPen, QBrush, QFont)
from PySide6.QtCore import QPointF, Qt

from fldesktop.include.widgets.flowlayout import FlowLayout
from fldesktop.include.widgets.terminal import Terminal as TerminalWidget
from fldesktop.include.widgets.isolated_webengine import IQWebEngineView

import base64
import locale


class Widget:
    def __init__(self, runner, name, props, parent) -> None:
        self._runner = runner
        self.name = name
        self.props = props
        self.parent = parent
        self.type = "widget"
        self.children = []

        self.callables = {}
    
    def _setup(self) -> None:
        self._setup_layouting()
        self._runner.widgets[self.name] = self
        self.update_props()

    def _setup_layouting(self) -> None:
        "Setups widget"

        # Im sorry...

        table_l = {
            "hlayout": QHBoxLayout,
            "vlayout": QVBoxLayout,
            "flayout": FlowLayout,
            "app": QVBoxLayout
        }

        table_w = {
            "widget": QWidget,
            "container": QScrollArea,
            "tabs": QTabWidget,
            "button": QPushButton,
            "label": QLabel,
            "checkbox": QCheckBox,
            "radiobutton": QRadioButton,
            "entry": QLineEdit,
            "textedit": QTextEdit,
            "webview": IQWebEngineView,
            "slider": QSlider,
            "terminal": TerminalWidget,
            "canvas": QWidget
        }

        print(self.type)

        # Create widget or layout

        if self.type in table_l:
            self.qlayout = table_l[self.type]()
        elif "stretch" in self.type:
            self.parent.qlayout.addStretch()
            return
        else:
            if self.type in table_w:
                self.qwidget = table_w[self.type]()
                if self.type == "container":
                    container = QWidget()
                    container.setAttribute(Qt.WA_DeleteOnClose, True)
                    self.qwidget.setWidgetResizable(True)
                    self.qwidget.setWidget(container)
                    if "direction" in self.props:
                        if self.props["direction"] == "ver":
                            self.qlayout = QVBoxLayout()
                        elif self.props["direction"] == "hor":
                            self.qlayout = QHBoxLayout()
                        elif self.props["direction"] == "flow":
                            self.qlayout = FlowLayout()
                        else:
                            self.qlayout = QVBoxLayout()
                    else:
                        self.qlayout = QVBoxLayout()
                    container.setLayout(self.qlayout)
            else:
                self.qwidget = QWidget()

        # Place widget or layout in widget or layout
        
        if self.parent:
            print(self.parent.type, self.parent, self.name)
            if self.parent.type in ["app", "vlayout", "hlayout",
                                    "flayout", "container"]:
                if "qwidget" in dir(self):
                    self.parent.qlayout.addWidget(self.qwidget)
                else:
                    self.parent.qlayout.addLayout(self.qlayout)
            else:
                if "qwidget" in dir(self):
                    self.qwidget.setParent(self.parent.qwidget)
                else:
                    self.parent.qwidget.setLayout(self.qlayout)
        
        if hasattr(self, "qwidget"):
            self.qwidget.setAttribute(Qt.WA_DeleteOnClose, True)
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

    def update_props(self):
        pass
    
    def update_children(self, tree: dict) -> None:
        "Replace children tree with a new one"

        if hasattr(self, "qlayout"):
            while self.qlayout.count():
                item = self.qlayout.takeAt(0)
                if item:
                    if widget := item.widget():
                        widget.deleteLater()
                    elif sub_layout := item.layout():
                        self.clear_layout_recursive(sub_layout)

        if hasattr(self, "qwidget"):
            children = self.qwidget.findChildren(QWidget)
            for widget in children:
                if widget != self.qwidget:
                    widget.deleteLater()

        self._runner.parser.build_tree_from_objects(tree, self)

    def clear_layout_recursive(self, layout) -> None:
        "Recursive layout clean"

        while layout.count():
            item = layout.takeAt(0)
            if widget := item.widget():
                widget.close()
            elif sub_layout := item.layout():
                self.clear_layout_recursive(sub_layout)
    
    def add_child(self, name: str, props: dict) -> None:

        if name:
            self._runner.parser.build_tree_from_objects({
                name: props
            }, self)
        else:
            self._runner.parser.build_tree_from_objects({
                "pidor": props
            }, self)
    
    def delete(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
            if hasattr(self.parent, "qlayout"):
                if hasattr(self, "qwidget"):
                    self.parent.qlayout.removeWidget(self.qwidget)
        if hasattr(self, "qwidget"):
            self.qwidget.setParent(None)
            self.qwidget.deleteLater()
        
        print("results", hasattr(self, "qwidget"))
    
    def tr(self, base_text: str) -> str:
        "Translate text"
        loc = locale.getlocale()[0]

        if loc in self._runner.translations:
            trs = self._runner.translations[loc]
            if base_text in trs:
                return trs[base_text]
        
        return base_text
        

class Button(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "button"

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False),
            "set_text": lambda t: self.qwidget.setText(str(t))
        }

        self._setup()

        if "text" in self.props:
            self.qwidget.setText(self.tr(str(self.props["text"])))
        if "icon" in self.props:
            self.qwidget.setIcon(QIcon.fromTheme(self.props["icon"]))
        if "flat" in self.props:
            self.qwidget.setFlat(self.props["flat"] == "true")

        self.qwidget.clicked.connect(
            lambda: self._runner.event(name=self.name, type="button_press")
        )


class VLayout(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "vlayout"
        print(self.type)
        self._setup()


class HLayout(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "hlayout"

        self._setup()


class FLayout(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "flayout"

        self._setup()


class Container(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "container"

        self._setup()


class Tabs(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "tabs"

        self.tabs = []

        self._setup()

        if "tabs" in self.props:
            for i in self.props["tabs"]:
                name = self.props["tabs"][i]["title"] if "title" in self.props["tabs"][i] else str(i)
                p = Container(self._runner, str(i), self.props["tabs"][i], {}, self)
                self._runner.parser.build_tree_from_objects(self.props["tabs"][i]["children"], p)
                self.qwidget.addTab(p.qwidget, name)
        
    def add_tab(self, name: str, props: dict):
        p = Container(self._runner, name, props, {}, self)
        self._runner.parser.build_tree_from_objects(props["children"], p)
        self.qwidget.addTab(p.qwidget, props["title"])


class Label(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "label"

        self.callables = {
            "set_text": self.set_text,
            "get_text": self.get_text
        }

        self._setup()

        if "text" in self.props:
            self.qwidget.setText(self.tr(str(self.props["text"])))
        if "alignment" in self.props:
            if self.props["alignment"] == "left":
                self.qwidget.setAlignment(Qt.AlignmentFlag.AlignLeft)
            elif self.props["alignment"] == "right":
                self.qwidget.setAlignment(Qt.AlignmentFlag.AlignRight)
            else:
                self.qwidget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if "style" in self.props:
            styles = {
                "caption": QFont("Noto Sans", 14, QFont.Bold),
                "header": QFont("Noto Sans", 12, QFont.Bold)
            }
            if self.props["style"] in styles:
                self.qwidget.setFont(styles[self.props["style"]])
    
    def get_text(self) -> str:
        return self.qwidget.toPlainText()

    def set_text(self, text: str) -> None:
        self.qwidget.setText(text)


class CheckBox(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "checkbox"

        self.callables = {
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

        if "text" in self.props:
            self.qwidget.setText(self.tr(str(self.props["text"])))


class RadioButton(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "radiobutton"

        self.callables = {
            "select": self.select,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

        if "text" in self.props:
            self.qwidget.setText(self.tr(str(self.props["text"])))

        self.qwidget.toggled.connect(
            lambda c: self._runner.event(
                name=self.name, type="radiobutton_select"
            ) if c else lambda: ...
        )
    
    def select(self, _):
        self.qwidget.blockSignals(True)
        self.qwidget.setChecked(True)
        self.qwidget.blockSignals(False)


class ImageView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "label"

        self.callables = {
            "set_image": self.set_image
        }

        self._setup()

        self.pixmap = QPixmap()
        self.qwidget.resizeEvent = self.resizeEvent
    
    def set_image(self, image: str) -> None:
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(base64.b64decode(image.encode()))
        self.qwidget.setPixmap(self.pixmap)
        self.resizeEvent(None)
    
    def resizeEvent(self, ev):
        self.qwidget.setPixmap(self.pixmap.scaled(self.qwidget.size(), 
                               Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                               Qt.TransformationMode.SmoothTransformation)
        )


class Icon(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "label"

        self.callables = {
            "set_icon": self.set_icon
        }

        self._setup()

        self.pixmap = QPixmap()

        if "icon" in self.props:
            self.set_icon({
                "icon": self.props["icon"],
                "width": self.props["width"]\
                    if "width" in self.props else 64,
                "height": self.props["height"]\
                    if "height" in self.props else 64,
            })
    
    def set_icon(self, args: dict) -> None:
        icon = QIcon.fromTheme(
            args["icon"] if "icon" in args else "none"
        )
        self.qwidget.setPixmap(icon.pixmap(
            args["width"] if "width" in args else 64,
            args["height"] if "height" in args else 64
        ))


class TextEdit(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "textedit"

        self.callables = {
            "set_text": self.set_text,
            "get_text": self.get_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()
    
    def get_text(self, _) -> str:
        return self.qwidget.toPlainText()

    def set_text(self, args) -> None:
        text = args["text"] if "text" in args else ""
        self.qwidget.setPlainText(text)


class Entry(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "entry"

        self.callables = {
            "get_text": self.get_text,
            "set_text": self.set_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()
    
    def get_text(self, _) -> str:
        return self.qwidget.text()

    def set_text(self, args):
        text = args["text"] if "text" in args else ""
        self.qwidget.setText(text)


class Slider(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "slider"

        self.callables = {
            "set_value": self.set_value,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

        if "orientation" in self.props:
            self.qwidget.setOrientation(
                Qt.Orientation.Vertical if self.props["orientation"] == "ver"\
                else Qt.Orientation.Horizontal
            )
        else:
            self.qwidget.setOrientation(Qt.Orientation.Horizontal)
        
        if "max_value" in self.props:
            self.qwidget.setMaximum(self.props["max_value"])
        
        if "min_value" in self.props:
            self.qwidget.setMinimum(self.props["min_value"])

        self.qwidget.valueChanged.connect(self.vc_handler)
    
    def vc_handler(self, value: int):
        
        self._runner.event(
            name=self.name, type="slider_value_changed", value=value
        )
    
    def set_value(self, data: dict):
        val = data["value"] if "value" in data else 0
        self.qwidget.setValue(val)


class Canvas(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "canvas"

        # Создаём растровый буфер
        self.pixmap = QPixmap(300, 300)
        self.pixmap.fill(Qt.transparent)
        
        # Настройки по умолчанию
        self.pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.brush = QBrush(Qt.NoBrush)
        self.bg_color = Qt.transparent

        self._setup()
    
    def setPen(self, pen):
        """Установить перо для последующих операций."""
        self.pen = pen
        
    def setBrush(self, brush):
        """Установить кисть для заполнения."""
        self.brush = brush
        
    def setBackgroundColor(self, color):
        """Изменить цвет фона (перезаполняет pixmap)."""
        self.bg_color = color
        self.pixmap.fill(color)
        self.update()
        
    def clear(self):
        """Очистить холст (заполнить цветом фона)."""
        self.pixmap.fill(self.bg_color)
        self.update()
        
    def rect(self, x, y, width, height, pen=None, brush=None):
        """Нарисовать прямоугольник."""
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        painter.setBrush(brush or self.brush)
        painter.drawRect(x, y, width, height)
        painter.end()
        self.update()
        
    def line(self, x1, y1, x2, y2, pen=None):
        """Нарисовать линию."""
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        painter.drawLine(x1, y1, x2, y2)
        painter.end()
        self.update()
        
    def circle(self, x, y, radius, pen=None, brush=None):
        """Нарисовать окружность (центр в x,y, радиус radius)."""
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        painter.setBrush(brush or self.brush)
        # drawEllipse принимает верхний левый угол и размеры
        painter.drawEllipse(x - radius, y - radius, 2 * radius, 2 * radius)
        painter.end()
        self.update()
        
    def bezier(self, p1, p2, p3, p4, pen=None):
        """Нарисовать кубическую кривую Безье по 4 точкам."""
        if isinstance(p1, tuple): p1 = QPointF(*p1)
        if isinstance(p2, tuple): p2 = QPointF(*p2)
        if isinstance(p3, tuple): p3 = QPointF(*p3)
        if isinstance(p4, tuple): p4 = QPointF(*p4)
            
        painter = QPainter(self.pixmap)
        painter.setPen(pen or self.pen)
        path = QPainterPath()
        path.moveTo(p1)
        path.cubicTo(p2, p3, p4)
        painter.drawPath(path)
        painter.end()
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)


class WebView(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "webview"

        self.callables = {
            "load_page": self.load_page,
            "reload": self.reload,
            "forward": self.forward,
            "back": self.back
        }

        self._setup()

        IQWebEngineView().titleChanged.connect(
            lambda t: self._runner.event(
            type="webview_page_title_changed", name=self.name,
            title=t)
        )
    
    def load_page(self, page: str):
        self.qwidget.setUrl(page)
    
    def reload(self) -> None:
        self.qwidget.reload()
    
    def forward(self) -> None:
        self.qwidget.forward()
    
    def back(self) -> None:
        self.qwidget.back()


class Terminal(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "terminal"

        self._setup()


class Stretch(Widget):
    def __init__(self, runner, name, props, parent):
        super().__init__(runner, name, props, parent)
        self.type = "stretch"

        self._setup()


class RootWidget(Widget):
    def __init__(self, runner):
        super().__init__(runner, "root", {}, None)
        self.type = "app"

        self._setup()
        self.qlayout = runner.main_layout


widget_table = {
    "vlayout": VLayout,
    "hlayout": HLayout,
    "flayout": FLayout,
    "tabs": Tabs,
    "stretch": Stretch,
    "container": Container,
    "label": Label,
    "image_view": ImageView,
    "icon": Icon,
    "checkbox": CheckBox,
    "radiobutton": RadioButton,
    "button": Button,
    "textedit": TextEdit,
    "entry": Entry,
    "slider": Slider,
    "webview": WebView,
    "terminal": Terminal
}
