#!/usr/bin/env python3
"""Generate the DescentBuddy icon PNG using PyQt6."""

import os
import sys

# Run from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

SIZE = 256
pixmap = QPixmap(SIZE, SIZE)
pixmap.fill(Qt.GlobalColor.transparent)

painter = QPainter(pixmap)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

# Background
grad = QLinearGradient(0, 0, SIZE, SIZE)
grad.setColorAt(0, QColor("#1e0800"))
grad.setColorAt(1, QColor("#080808"))
painter.setBrush(grad)
painter.setPen(Qt.PenStyle.NoPen)
painter.drawRoundedRect(0, 0, SIZE, SIZE, 32, 32)

# Outer orange ring
pen = QPen(QColor("#e85c00"), 10)
painter.setPen(pen)
painter.setBrush(Qt.BrushStyle.NoBrush)
painter.drawEllipse(14, 14, SIZE - 28, SIZE - 28)

# Inner dark ring
pen2 = QPen(QColor("#3a1800"), 4)
painter.setPen(pen2)
painter.drawEllipse(26, 26, SIZE - 52, SIZE - 52)

# "D" letter — large, centred
painter.setPen(QColor("#ff7a1a"))
font = QFont("Arial", 110, QFont.Weight.Bold)
painter.setFont(font)
painter.drawText(pixmap.rect().adjusted(0, -8, 0, 0), Qt.AlignmentFlag.AlignCenter, "D")

# Small "B" superscript bottom-right
painter.setPen(QColor("#cc1a00"))
font2 = QFont("Arial", 44, QFont.Weight.Bold)
painter.setFont(font2)
painter.drawText(
    0, SIZE // 2, SIZE - 18, SIZE // 2 - 10,
    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
    "B",
)

painter.end()

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "descentbuddy.png")
pixmap.save(out_path, "PNG")
print(f"Icon saved → {out_path}")
