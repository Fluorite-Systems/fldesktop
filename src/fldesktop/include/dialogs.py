from PySide6.QtWidgets import (QWidget, QFileDialog, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QEvent, Signal


class FileDialog(QWidget):
    # Сигналы
    fileSelected = Signal(list)      # Выбран(ы) пути
    cancelled = Signal()              # Диалог закрыт без выбора

    def __init__(self, mode: str, parent=None):
        super().__init__(parent)
        self.mode = mode
        self._setup_ui()

    def _setup_ui(self):
        # Базовый QFileDialog в режиме виджета
        self.dialog = QFileDialog()
        self.dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        self.dialog.setWindowFlags(Qt.WindowType.Widget)

        # Настройка в зависимости от режима
        if self.mode == "open_file":
            self.dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            self.dialog.setLabelText(QFileDialog.DialogLabel.FileName, "Файл:")
        
        elif self.mode == "save_file":
            self.dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            self.dialog.setLabelText(QFileDialog.DialogLabel.FileName, "Сохранить как:")
        
        elif self.mode == "open_folder".SELECT_FOLDER:
            self.dialog.setFileMode(QFileDialog.FileMode.Directory)
            self.dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            self.dialog.setLabelText(QFileDialog.DialogLabel.FileName, "Папка:")

        # Подключение сигналов
        self.dialog.fileSelected.connect(self._on_file_selected)
        self.dialog.rejected.connect(self._on_cancelled)

        # Макет виджета
        layout = QVBoxLayout(self)
        layout.addWidget(self.dialog)
        self.setLayout(layout)

    def _on_file_selected(self, file: str):
        self.fileSelected.emit([file])

    def _on_cancelled(self):
        self.cancelled.emit()

    # Публичные методы для настройки
    def set_directory(self, path: str):
        """Установить начальную директорию."""
        self.dialog.setDirectory(path)

    def set_name_filter(self, filter: str):
        """Установить фильтр файлов (например, 'Images (*.png *.jpg)')."""
        self.dialog.setNameFilter(filter)

    def select_file(self, filename: str):
        """Предвыбрать имя файла (актуально для SAVE_FILE)."""
        if self.mode == "save_file":
            self.dialog.selectFile(filename)

    def get_current_directory(self) -> str:
        """Получить текущую директорию в диалоге."""
        return self.dialog.directory().path()

    def clear_selection(self):
        """Сбросить текущее выделение."""
        self.dialog.selectFile("")


class MessageBox(QWidget):
    def __init__(self, type: str, contents: str):
        super().__init__()

        self.type = type

        self.layout = QHBoxLayout(self)
        self.label = QLabel(str(contents))
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.icon = QLabel()
        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.label)
        self.layout.addStretch()

        self.setup_icon()
    
    def setup_icon(self):
        icons = {
            "error": "dialog-error",
            "syserror": "dialog-error",
            "information": "dialog-information",
            "success": "dialog-positive"
        }

        self.qicon = QIcon.fromTheme(icons[self.type])

        self.icon.setPixmap(
            QIcon.fromTheme(icons[self.type]).pixmap(64, 64)
        )


class DialogManager:
    def __init__(self, comm):
        
        self.comm = comm
        self.desktop = self.comm.request("desktkop", "get_instance")

        self.comm.register("dialogmgr", {
            "notification": self.notify,
            "error": self.error,
            "sys_error": self.sys_error,
            "open_file": self.file_chooser,
            "save_file": self.save_file_chooser
        })
    
    def notify(self, message):
        pass

    def file_chooser(self, on_choosen):

        diag = FileDialog("open_file")
        diag.fileSelected.connect(on_choosen)
        
        id = self.comm.request(
            "wm", "create_window", {
                "widget": diag,
                "name": "Выбор файла",
                "icon": QIcon.fromTheme("applications-other")
            }
        )[0]

        diag.fileSelected.connect(lambda x, i=id: self.comm.request(
            "wm", "close_window", i
        ))
        diag.cancelled.connect(lambda i=id: self.comm.request(
            "wm", "close_window", i
        ))
    
    def save_file_chooser(self, on_choosen):

        diag = FileDialog("save_file")
        diag.fileSelected.connect(on_choosen)
        
        id = self.comm.request(
            "wm", "create_window", {
                "widget": diag,
                "name": "Сохранение файла",
                "icon": QIcon.fromTheme("applications-other")
            }
        )[0]

        diag.fileSelected.connect(lambda x, i=id: self.comm.request(
            "wm", "close_window", i
        ))
        diag.cancelled.connect(lambda i=id: self.comm.request(
            "wm", "close_window", i
        ))
    
    def error(self, title: str, contents: str):

        diag =  MessageBox("error", contents)

        id = self.comm.request(
            "wm", "create_window", {
                "widget": diag,
                "name": str(title),
                "icon": diag.qicon,
                "type": "messagebox"
            }
        )

    def sys_error(self, contents: str):

        diag = MessageBox("syserror", contents)

        self.comm.request(
            "wm", "create_window",
            "System error", diag,
            size=(300, 200),
            type="messagebox"
        )