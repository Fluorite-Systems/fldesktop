from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Slot

from fldesktop.include.widgets.isolator import GraphicsIsolatedWidget

from pathlib import Path

class Terminal(GraphicsIsolatedWidget):
    def __init__(self, parent=None):

        self.quick_widget = QQuickWidget()

        super().__init__(self.quick_widget, parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.quick_widget.setSource(QUrl.fromLocalFile(
            (Path(__file__).absolute().parent / "terminal.qml").as_posix()
        ))
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        
        self.layout.addWidget(self.quick_widget)
        
        self._qml_object = None
        #self.quick_widget.rootObjectChanged.connect(self._on_root_object_changed)
        
    def _on_root_object_changed(self):
        """Когда QML объект загружен, сохраняем ссылку на него"""
        self._qml_object = self.quick_widget.rootObject()
        
    def get_qml_object(self):
        """Возвращает QML объект для прямого доступа"""
        return self._qml_object
    
    @Slot(str)
    def set_font_family(self, family: str):
        """Установить семейство шрифта"""
        if self._qml_object:
            self._qml_object.setProperty("fontFamily", family)
            
    @Slot(int)
    def set_font_size(self, size: int):
        """Установить размер шрифта"""
        if self._qml_object:
            self._qml_object.setProperty("fontSize", size)
            
    @Slot(str)
    def set_font(self, family: str, size: int):
        """Установить шрифт (семейство и размер)"""
        self.set_font_family(family)
        self.set_font_size(size)
        
    @Slot(str)
    def set_color_scheme(self, scheme: str):
        """Установить цветовую схему (dark, light и т.д.)"""
        if self._qml_object:
            self._qml_object.setProperty("colorScheme", scheme)
            
    @Slot(str)
    def set_background_color(self, color: str):
        """Установить цвет фона (например, '#1e1e1e')"""
        if self._qml_object:
            self._qml_object.setProperty("backgroundColor", color)
            
    @Slot(str)
    def set_foreground_color(self, color: str):
        """Установить цвет текста (например, '#ffffff')"""
        if self._qml_object:
            self._qml_object.setProperty("foregroundColor", color)
            
    @Slot(str)
    def set_working_directory(self, directory: str):
        """Установить рабочую директорию"""
        if self._qml_object and hasattr(self._qml_object, 'session'):
            session = self._qml_object.property("session")
            if session:
                session.setProperty("initialWorkingDirectory", directory)
                
    @Slot()
    def start_shell(self):
        """Запустить оболочку"""
        if self._qml_object and hasattr(self._qml_object, 'startShellProgram'):
            self._qml_object.startShellProgram()
            
    @Slot(str)
    def execute_command(self, command: str):
        """Выполнить команду в терминале"""
        if self._qml_object and hasattr(self._qml_object, 'sendText'):
            self._qml_object.sendText(command + "\n")
            
    @Slot()
    def clear(self):
        """Очистить терминал"""
        if self._qml_object and hasattr(self._qml_object, 'clear'):
            self._qml_object.clear()
            
    @Slot()
    def copy(self):
        """Копировать выделенный текст"""
        if self._qml_object and hasattr(self._qml_object, 'copyClipboard'):
            self._qml_object.copyClipboard()
            
    @Slot()
    def paste(self):
        """Вставить текст из буфера обмена"""
        if self._qml_object and hasattr(self._qml_object, 'pasteClipboard'):
            self._qml_object.pasteClipboard()
            
    @Slot(int)
    def set_opacity(self, opacity: float):
        """Установить прозрачность (0.0 - 1.0)"""
        if self._qml_object:
            self._qml_object.setProperty("opacity", opacity)
            
    @Slot(bool)
    def set_blinking_cursor(self, enabled: bool):
        """Включить/выключить мигающий курсор"""
        if self._qml_object:
            self._qml_object.setProperty("blinkingCursor", enabled)
            
    @Slot(int)
    def set_scrollback_lines(self, lines: int):
        """Установить количество строк буфера прокрутки"""
        if self._qml_object:
            self._qml_object.setProperty("scrollbackLines", lines)
    
    @Slot(str)
    def set_terminal_title(self, title: str):
        """Установить заголовок терминала"""
        if self._qml_object:
            self._qml_object.setProperty("title", title)