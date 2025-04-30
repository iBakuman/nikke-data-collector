from dataclasses import dataclass

from PySide6.QtGui import QColor


@dataclass
class Color:
    r: int
    g: int
    b: int

    def to_q_color(self)->QColor:
        return QColor(self.r, self.g, self.b)