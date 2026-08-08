from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QWidget

import math
import random
from typing import Any


class ConfettiItem(QGraphicsItem):
    __slots__ = (
        "vx",
        "vy",
        "rot_speed",
        "fade_speed",
        "alpha",
        "color",
        "size",
        "shape_type",
        "_boundingRect",
    )

    def __init__(self, x: float, y: float, side: str) -> None:
        super().__init__()
        self.setPos(x, y)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setCacheMode(QGraphicsItem.NoCache)

        if side == "left":
            angle = random.uniform(math.pi * 1.5, math.pi * 1.8)
        else:
            angle = random.uniform(math.pi * 1.2, math.pi * 1.5)

        speed = random.randint(10, 40)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.setRotation(random.uniform(0.0, 360.0))
        self.rot_speed = random.uniform(-14.0, 14.0)

        self.color: QColor = QColor(
            random.randint(75, 255),
            random.randint(75, 255),
            random.randint(75, 255),
        )
        self.size = random.uniform(6.0, 16.0)
        self.shape_type = random.choice([0, 1])

        self.alpha = 1.0
        self.fade_speed = random.uniform(0.012, 0.026)

        half = self.size / 2.0
        self._boundingRect: QRectF = QRectF(-half, -half, self.size, self.size)

    def boundingRect(self) -> QRectF:
        return self._boundingRect

    def advance(self, phase: int) -> None:
        if not phase:
            return

        self.vy += 0.52
        self.vx *= 0.955
        self.vy *= 0.955

        self.vx += math.sin(self.pos().y() * 0.05) * 0.15

        self.moveBy(self.vx, self.vy)
        self.setRotation(self.rotation() + self.rot_speed)

        self.alpha -= self.fade_speed

        if self.alpha <= 0:
            self.setFlag(QGraphicsItem.ItemHasNoContents, True)
            scene: QGraphicsScene | None = self.scene()
            if scene:
                scene.removeItem(self)

    def paint(self, painter: QPainter, option: Any, widget: QWidget | None = None) -> None:
        painter.setPen(Qt.NoPen)
        painter.setOpacity(max(0.0, self.alpha))
        painter.setBrush(self.color)

        half = self.size / 2.0
        if self.shape_type == 0:
            painter.drawRect(-half, -half, self.size, self.size * 0.65)
        else:
            painter.drawEllipse(-half, -half, self.size, self.size)


class ConfettiEffect(QGraphicsView):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.scene: QGraphicsScene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setInteractive(False)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing, False)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setStyleSheet("background: transparent; border: none;")

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.scene.advance)
        self.timer.start(33)

        QTimer.singleShot(4000, self.close)

        self.show()
        self.raise_()

        parent_size = self.parent().size()
        self.resize(parent_size)
        self.scene.setSceneRect(0, 0, parent_size.width(), parent_size.height())

        self.spawn_wave(25)
        QTimer.singleShot(60, lambda: self.spawn_wave(20))
        QTimer.singleShot(140, lambda: self.spawn_wave(20))
        QTimer.singleShot(240, lambda: self.spawn_wave(15))

    def spawn_wave(self, count_per_side: int) -> None:
        if not self.isVisible():
            return

        spawn_y = self.height() // 3 * 2
        width = float(self.width())

        for _ in range(count_per_side):
            self.scene.addItem(ConfettiItem(0.0, spawn_y, "left"))
            self.scene.addItem(ConfettiItem(width, spawn_y, "right"))


class WindowEffects:

    def __init__(self, window: QWidget) -> None:
        self.window: QWidget = window
        self._effects: list[ConfettiEffect] = []

    def effect(self, type: str) -> None:
        match type:
            case "confetti":
                if self._effects:
                    for old_effect in list(self._effects):
                        old_effect.close()

                e: ConfettiEffect = ConfettiEffect(self.window)
                self._effects.append(e)
                e.destroyed.connect(
                    lambda: self._effects.remove(e) if e in self._effects else None
                )
            case _:
                pass
