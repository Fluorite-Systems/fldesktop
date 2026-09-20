from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QDrag, QPixmap
from PySide6.QtCore import Qt, QMimeData, QObject, QEvent, QPoint, QByteArray


class DragFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_position = QPoint()

    def eventFilter(self, watched, event):
        if not watched.property("drag_enabled"):
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            return False

        elif event.type() == QEvent.Type.MouseMove and (event.buttons() & Qt.MouseButton.LeftButton):
            if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
                return False

            custom_data = watched.property("drag_data")
            if custom_data is None:
                custom_data = ""

            mime_type = watched.property("drag_mime_type") or "text/plain"

            mime_data = QMimeData()
            
            if mime_type == "text/plain":
                mime_data.setText(str(custom_data))
            else:
                byte_array = QByteArray(str(custom_data).encode("utf-8"))
                mime_data.setData(mime_type, byte_array)

            drag = QDrag(watched)
            drag.setMimeData(mime_data)
            
            pixmap = QPixmap(watched.size())
            pixmap.fill(Qt.GlobalColor.transparent)
            watched.render(pixmap, QPoint(), renderFlags=QWidget.RenderFlag.DrawChildren)

            drag.setPixmap(pixmap)
            drag.setHotSpot(self.drag_start_position)

            drag.exec(Qt.DropAction.CopyAction)
            return True
                
        return super().eventFilter(watched, event)


class DropFilter(QObject):
    def eventFilter(self, watched, event):
        if not watched.property("drop_enabled"):
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.DragEnter:
            mime_data = event.mimeData()
            allowed_types = watched.property("drop_mime_types") or []

            has_valid_format = any(mime_data.hasFormat(m_type) for m_type in allowed_types)
            
            if has_valid_format:
                event.acceptProposedAction()
                return True
            else:
                event.ignore()

        elif event.type() == QEvent.Type.Drop:
            mime_data = event.mimeData()
            allowed_types = watched.property("drop_mime_types") or []

            for m_type in allowed_types:
                if mime_data.hasFormat(m_type):

                    if m_type == "text/plain":
                        received_text = mime_data.text()
                    else:
                        received_text = bytes(mime_data.data(m_type)).decode("utf-8")
                    
                    callback = watched.property("drop_callback")
                    if callback and callable(callback):
                        callback(received_text, m_type)
                        
                    event.acceptProposedAction()
                    return True

        return super().eventFilter(watched, event)
