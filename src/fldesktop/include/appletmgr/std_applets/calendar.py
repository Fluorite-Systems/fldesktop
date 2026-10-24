from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt, QPoint, QTimer, QTime, QTime

from fldesktop.include.uikit.applet import Applet
from fldesktop.include.thememgr import STD_COLORS


class AnalogueClock(QWidget):
    def __init__(self):
        super().__init__()

    def paintEvent(self, event) -> None:
        side = min(self.width(), self.height())
        self.draw_clock(side)

    def draw_clock(self, side: int) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        scale = side / 200.0
        painter.scale(scale, scale)

        px = 1.0 / scale

        self.draw_face(painter)
        self.draw_ticks(painter, side, px)
        self.draw_hands(painter, side, px)

        painter.end()

    def draw_face(self, painter: QPainter) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(STD_COLORS["darkblack"]))
        painter.drawEllipse(QPoint(0, 0), 96, 96)

    def draw_ticks(self, painter: QPainter, side: int, px: float) -> None:
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

    def draw_hands(self, painter: QPainter, side: int, px: float) -> None:
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


class CalWidget(QWidget):
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
        font = self.time_lbl.font()
        font.setBold(True)
        font.setPointSize(16)
        self.time_lbl.setFont(font)
        self.clock_tile_l.addWidget(self.time_lbl)

        self.layout.addWidget(self.clock_tile)

    def refresh(self):

        self.clock.update()

        self.time_lbl.setText(
            QTime.currentTime().toString("hh:mm")
        )


class Calendar(Applet):
    def __init__(self, comm):
        super().__init__(comm, "", {})

        self.cal = CalWidget(comm)
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