from PySide6.QtWidgets import QLayout
from PySide6.QtCore import Qt, QRect, QSize


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._item_list = []
        self._v_spacing = 6
        self.setContentsMargins(0, 0, 0, 0)

    def __del__(self):
        while self.takeAt(0):
            pass

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect):
        self.invalidate()
        super().setGeometry(rect)
        self._do_layout(rect, True)

    def sizeHint(self):
        return self._minimum_size()

    def minimumSize(self):
        return self._minimum_size()

    def _do_layout(self, rect, apply_geometry):
        l, t, r, b = self.getContentsMargins()
        eff_rect = rect.adjusted(+l, +t, -r, -b)

        if not self._item_list:
            return t + b

        # Базовый шаг для первоначального разбиения рядов
        base_h = 6.0 + (eff_rect.width() * 0.02)

        # Шаг 1: Первичное распределение по строкам
        rows = []
        current_row = []
        current_width = base_h

        for item in self._item_list:
            w = item.sizeHint().width()
            if current_width + w + base_h > eff_rect.width() and current_row:
                rows.append(current_row)
                current_row = [item]
                current_width = base_h + w + base_h
            else:
                current_row.append(item)
                current_width += w + base_h

        if current_row:
            rows.append(current_row)

        # Шаг 2: Позиционирование элементов с синхронизацией отступа
        y = eff_rect.y() + self._v_spacing
        last_filled_spacing = None  # Переменная для запоминания эталонного отступа

        for idx, row in enumerate(rows):
            line_height = max(item.sizeHint().height() for item in row)
            total_widgets_width = sum(item.sizeHint().width() for item in row)
            
            slots = len(row) + 1
            available_space = eff_rect.width() - total_widgets_width

            if idx == len(rows) - 1 and last_filled_spacing is not None:
                # Если это последняя строка, жестко берем отступ из предыдущей строки
                h_spacing = last_filled_spacing
            elif available_space > 0:
                h_spacing = available_space / slots
                # Запоминаем этот отступ как эталон для следующих строк
                last_filled_spacing = h_spacing
            else:
                h_spacing = base_h

            x = float(eff_rect.x() + h_spacing)

            for item in row:
                w = item.sizeHint().width()
                h = item.sizeHint().height()

                if apply_geometry:
                    item.setGeometry(QRect(int(x), y, w, h))

                x += w + h_spacing

            y += line_height + self._v_spacing

        return y - rect.y() + b

    def _minimum_size(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        l, t, r, b = self.getContentsMargins()
        return size + QSize(l + r, t + b)
