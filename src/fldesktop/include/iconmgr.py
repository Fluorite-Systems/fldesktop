from PySide6.QtGui import QIcon, QPainter, QPixmap, QPen, QColor, QPolygon
from PySide6.QtCore import Qt, QRect, QPoint

from pathlib import Path
import logging


DEFAULTS = {
    "color": "fg",
    "outline": "fg",
    "fill": None,
    "width": 10,
    "rounding": 14,
    "cap": "square",
    "x": 0,
    "y": 0,
    "x1": 0,
    "x2": 0,
    "y1": 0,
    "y2": 0,
    "w": 0,
    "h": 0
}


class Parser:
    def __init__(self, comm) -> None:
        self.comm = comm

        self.palette = self.comm.request(
            "thememgr", "stdcolors"
        )

    def parse(self, code) -> list:

        objects = []

        for l in code.splitlines():
            if l:
                spl = l.split()
                if len(spl) >= 2:
                    t = spl.pop(0)

                    obj = {
                        "type": t,
                        "values": {}
                    }

                    for expr in spl:
                        if "=" in expr:
                            se = expr.split("=")
                            if len(se) == 2:
                                obj["values"][se[0]] = se[1]

                    objects.append(obj)

        return objects
    
    def rectify(self, objects: list) -> list:

        for obj in objects:
            for val in obj["values"]:
                if val in ["width", "r", "rounding"]:
                    obj["values"][val] = int(obj["values"][val])
                if val in ["w", "h"]:
                     obj["values"][val] = int(obj["values"][val]) - 1

            c = 0
            f = True
            while f:
                x = f"x{c if c else ""}"
                y = f"y{c if c else ""}"
                if x in obj["values"] or y in obj["values"]:
                    if x in obj["values"]:
                        obj["values"][x] = int(obj["values"][x]) + 1
                    if y in obj["values"]:
                        obj["values"][y] = int(obj["values"][y]) + 1
                    c += 1
                else:
                    if c:
                        f = False
                    else:
                        c += 1

            for i in DEFAULTS:
                if not i in obj["values"]:
                    obj["values"][i] = DEFAULTS[i]

            for z in ["color", "outline", "fill"]:

                if obj["values"][z] in self.palette:
                    obj["values"][z] = self.palette[obj["values"][z]]
                else:
                    if obj["values"][z]:
                        obj["values"][z] = self.palette["fg"]

        return objects
        
    def iconify(self, objects: list, size: int = 256, grid: bool = False) -> QIcon:

        mul = round(size / 16)

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if grid:
            for x in range(1, 16):
                for y in range(1, 16):
                    painter.setPen(QPen(QColor(Qt.gray), 5))
                    painter.setBrush(Qt.gray)     
                    painter.drawEllipse(
                        x * mul - 2, y * mul - 2, 4, 4
                    )

        for obj in objects:
            v = obj["values"]
            match obj["type"]:
                case "rectangle":
                    painter.setPen(QPen(QColor(v["outline"]), v["width"] + 0.0001))
                    painter.setBrush(QColor(v["fill"]) if v["fill"] else Qt.NoBrush)       
                    painter.drawRoundedRect(
                        QRect(
                            v["x"] * mul, v["y"] * mul, v["w"] * mul, v["h"] * mul
                        ), v["rounding"], v["rounding"]
                    )

                case "circle":
                    painter.setPen(QPen(QColor(v["outline"]), v["width"]))
                    painter.setBrush(QColor(v["fill"]) if v["fill"] else Qt.NoBrush)
                    painter.drawEllipse(
                        v["x"] * mul - v["r"] * mul, v["y"] * mul - v["r"] * mul,
                        v["r"] * mul * 2, v["r"] * mul * 2
                    )

                case "line":
                    pen = QPen(QColor(v["outline"]), v["width"])
                    
                    if v["cap"] == "rounded":
                        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    elif v["cap"] == "none":
                        pen.setCapStyle(Qt.PenCapStyle.FlatCa)

                    painter.setPen(pen)
                    painter.setBrush(QColor(v["fill"]) if v["fill"] else Qt.NoBrush)

                    painter.drawLine(
                        v["x1"] * mul, v["y1"] * mul, v["x2"] * mul, v["y2"] * mul
                    )

                case "polygon":
                    points = []
                    c = 1
                    f = True
                    while f:
                        if f"x{c}" in v and f"y{c}" in v:
                            points.append(QPoint(v[f"x{c}"] * mul, v[f"y{c}"] * mul))
                            c += 1
                        else:
                            f = False
                    print(points)

                    painter.setPen(QPen(QColor(v["outline"]), v["width"]))
                    painter.setBrush(QColor(v["fill"]) if v["fill"] else Qt.NoBrush)
                    polygon = QPolygon(points)
                    painter.drawPolygon(polygon)

        painter.end()

        return QIcon(pixmap)


class IconManager:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register(
            "iconmgr",
            {
                "get": self.get_icon,
                "load": self.load_icon,
                "parse": self.parse
            }
        )

        self.parser = Parser(self.comm)

        self.load_std_icons()

    def get_icon(self, name: str):
        
        if name in self.icons:
            return self.icons[name]
        else:
            logging.warning(f"Requested icon that does not exists: {name}")
            return QIcon()

    def load_icon(self, path: Path) -> QIcon:

        with open(path) as f:
            code = f.read()

        icon = self.parser.iconify(
            self.parser.rectify(
                self.parser.parse(code)
            )
        )

        return icon
    
    def parse(self, code: str) -> QIcon:

        icon = self.parser.iconify(
            self.parser.rectify(
                self.parser.parse(code)
            )
        )

        return icon

    def load_std_icons(self):

        self.icons = {}

        path = Path(__file__).resolve().parent / "assets" / "icons"

        for i in path.iterdir():
            if i.suffix == ".fvgi":

                try:
                
                    with open(i) as f:
                        icon = self.parser.iconify(
                            self.parser.rectify(
                                self.parser.parse(
                                    f.read()
                                )
                            )
                        )
                except Exception as e:
                    logging.warning(f"Failed to load icon {i.stem}: {e}")
                    icon = QIcon()

                self.icons[i.stem] = icon
