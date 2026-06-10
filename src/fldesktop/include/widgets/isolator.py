from PySide6.QtWidgets import (QWidget, QGraphicsView, QVBoxLayout,
                               QGraphicsScene)


class GraphicsIsolatedWidget(QWidget):
    """
    Виджет-контейнер, который изолирует OpenGL-виджет внутри QGraphicsScene.
    Это создаёт дополнительный слой композиции и может устранить тормоза.
    """
    
    def __init__(self, content_widget: QWidget, parent=None):
        super().__init__(parent)
        
        # Создаём сцену и вид представления
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("""
            QGraphicsView {
                background: transparent;
                border: none;
            }
        """)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Помещаем виджет в сцену через прокси
        self.proxy = self.scene.addWidget(content_widget)
        
        # Настраиваем размеры
        self.proxy.setGeometry(0, 0, content_widget.width(), content_widget.height())
        self.view.setSceneRect(0, 0, content_widget.width(), content_widget.height())
        
        # Компоновка
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        
        # Сохраняем ссылку на внутренний виджет
        self.content_widget = content_widget
    
    def resizeEvent(self, event):
        """При изменении размера контейнера — подгоняем сцену и прокси"""
        super().resizeEvent(event)
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.view.setSceneRect(0, 0, self.width(), self.height())
        if hasattr(self, 'proxy'):
            self.proxy.setGeometry(0, 0, self.width(), self.height())
            if hasattr(self.content_widget, 'resize'):
                self.content_widget.resize(self.width(), self.height())
