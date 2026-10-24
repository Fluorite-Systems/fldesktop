from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QSizePolicy)
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtCore import (Qt, QPoint, QTimer, QTime, QTime, QRect, QLocale)

from fldesktop.include.uikit.applet import Applet
from fldesktop.include.thememgr import STD_COLORS

from datetime import date


class AnalogueClock(QWidget):
    def __init__(self):
        super().__init__()

    def paintEvent(self, event) -> None:
        side = min(self.width(), self.height())
        self._draw_clock(side)

    def _draw_clock(self, side: int) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        scale = side / 200.0
        painter.scale(scale, scale)

        px = 1.0 / scale

        self._draw_face(painter)
        self._draw_ticks(painter, side, px)
        self._draw_hands(painter, side, px)

        painter.end()

    def _draw_face(self, painter: QPainter) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(STD_COLORS["darkblack"]))
        painter.drawEllipse(QPoint(0, 0), 96, 96)

    def _draw_ticks(self, painter: QPainter, side: int, px: float) -> None:
        step = 5 if side < 140 else 1
        for i in range(0, 60, step):
            painter.save()
            painter.rotate(6 * i)
            if i % 5 == 0:
                w = max(1.0, 2.0 * px)
                painter.setPen(QPen(QColor(STD_COLORS["white"]), w))
                inner = -82 if side >= 120 else -80
                painter.drawLine(0, -88, 0, inner)
            else:
                w = max(1.0, 1.0 * px)
                painter.setPen(QPen(QColor("#4a4a4a"), w))
                painter.drawLine(0, -88, 0, -86)
            painter.restore()

    def _draw_hands(self, painter: QPainter, side: int, px: float) -> None:
        time = QTime.currentTime()

        hour_len = -50 if side >= 140 else -46
        min_len = -75 if side >= 140 else -70
        sec_len = -85 if side >= 140 else -80

        painter.save()
        painter.rotate(30.0 * (time.hour() + time.minute() / 60.0))
        painter.setPen(QPen(QColor(STD_COLORS["lightwhite"]),
                            max(2.0, 3.5 * px), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, 6, 0, hour_len)
        painter.restore()

        painter.save()
        painter.rotate(6.0 * (time.minute() + time.second() / 60.0))
        painter.setPen(QPen(QColor(STD_COLORS["darkwhite"]),
                            max(1.5, 2.5 * px), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, 8, 0, min_len)
        painter.restore()

        painter.save()
        painter.rotate(6.0 * time.second())
        painter.setPen(QPen(QColor(STD_COLORS["red"]),
                            max(1.0, 1.5 * px), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, 12, 0, sec_len)
        painter.restore()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(STD_COLORS["red"]))
        r = 3.5 if side >= 140 else 2.5
        painter.drawEllipse(QPoint(0, 0), r, r)


class CalendarWidget(QWidget):
    def __init__(self, locale: QLocale | None = None) -> None:
        super().__init__()
        self._locale = locale or QLocale()
        self.setMinimumSize(80, 70)

    def setLocale(self, locale: QLocale) -> None:
        self._locale = locale
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._draw(painter, date.today())
        painter.end()

    def _draw(self, painter: QPainter, today: date) -> None:
        w, h = self.width(), self.height()
        painter.translate(w / 2, h / 2)
        self._draw_header(painter, today, w, h)
        self._draw_grid(painter, today, w, h)

    def _draw_header(self, painter: QPainter, today: date, w: int, h: int) -> None:
        month = self._locale.standaloneMonthName(today.month, QLocale.LongFormat)
        if month:
            month = month[0].upper() + month[1:]
        title = f"{month} {today.year}"

        font = QFont()
        font.setPointSizeF(max(6.0, h * 0.06))
        font.setBold(True)
        painter.setFont(font)

        header_h = h * 0.14
        painter.setPen(QPen(QColor(STD_COLORS["white"])))
        painter.drawText(
            QRect(int(-w / 2), int(-h / 2), w, int(header_h)),
            Qt.AlignCenter,
            title,
        )

    def _draw_grid(self, painter: QPainter, today: date, w: int, h: int) -> None:
        first_dow = self._locale.firstDayOfWeek()
        first_idx = int(first_dow.value) - 1

        grid_top = -h / 2 + h * 0.14
        grid_left = -w / 2 + w * 0.04
        grid_w = w * 0.92
        grid_h = h - h * 0.14 - h * 0.02
        cell_w = grid_w / 7.0
        cell_h = grid_h / 6.0

        font_wd = QFont()
        font_wd.setPointSizeF(max(4.5, cell_h * 0.4))
        painter.setFont(font_wd)

        for col in range(7):
            qt_dow = (first_idx + col) % 7 + 1
            name = (
                self._locale.dayName(qt_dow, QLocale.ShortFormat)
                or self._locale.dayName(qt_dow, QLocale.NarrowFormat)
            )
            is_weekend = qt_dow in (Qt.Saturday.value, Qt.Sunday.value)
            color = STD_COLORS["darkwhite"] if is_weekend else STD_COLORS["white"]

            x = grid_left + col * cell_w
            rect = QRect(int(x), int(grid_top), int(cell_w), int(cell_h))
            painter.setPen(QPen(QColor(color)))
            painter.drawText(rect, Qt.AlignCenter, name)

        first = today.replace(day=1)
        offset = (first.weekday() - first_idx) % 7

        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        days_in_month = (next_month - first).days

        font_num = QFont()
        font_num.setPointSizeF(max(5, cell_h * 0.45))
        painter.setFont(font_num)

        for d in range(days_in_month):
            idx = offset + d
            row, col = divmod(idx, 7)
            x = grid_left + col * cell_w
            y = grid_top + (row + 1) * cell_h
            cell = QRect(int(x), int(y), int(cell_w), int(cell_h))

            qt_dow = (first_idx + col) % 7 + 1
            is_weekend = qt_dow in (Qt.Saturday.value, Qt.Sunday.value)
            is_today = (d + 1 == today.day)

            if is_today:
                painter.setPen(QPen(QColor(STD_COLORS["blue"])))
            elif is_weekend:
                painter.setPen(QPen(QColor(STD_COLORS["red"])))
            else:
                painter.setPen(QPen(QColor(STD_COLORS["white"])))

            painter.drawText(cell, Qt.AlignCenter, self._locale.toString(d + 1))


class CalContainer(QWidget):
    def __init__(self, comm):
        super().__init__()

        self.comm = comm

        self.layout = QVBoxLayout(self)

        self.clock_tile = QWidget()
        self.clock_tile_l = QHBoxLayout(self.clock_tile)

        self.clock = AnalogueClock()
        self.clock_tile_l.addWidget(self.clock)

        self.time_lbl = QLabel(wordWrap=True)
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        font = self.time_lbl.font()
        font.setBold(True)
        font.setPointSize(16)
        self.time_lbl.setFont(font)
        self.clock_tile_l.addWidget(self.time_lbl)

        self.layout.addWidget(self.clock_tile)

        self.cal = CalendarWidget()
        self.layout.addWidget(self.cal)

        self.refresh()

    def refresh(self):

        self.clock.update()

        self.time_lbl.setText(
            QTime.currentTime().toString("hh:mm")
        )


class Calendar(Applet):
    def __init__(self, comm):
        super().__init__(comm, "", {})

        self.cal = CalContainer(comm)
        self.cal.setMaximumSize(350, 300)
        self.cal.setMinimumSize(100, 100)
        self.qlayout.addWidget(self.cal)
        self.qlayout.setContentsMargins(5, 5, 5, 5)

        self.widget.setMaximumSize(self.cal.width() + 5, self.cal.height() + 5)

        self.menu.sync_size()

        self.timer = QTimer(interval=1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()


    def refresh(self):

        text = QTime.currentTime().toString("hh:mm")

        self.attrs["Attr.UI.Applet.ButtonText"] = text
        self.apply_attrs()

        self.cal.refresh()