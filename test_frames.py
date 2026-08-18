import json
import os
from PySide6.QtGui import QImage

frame_width = 300
frame_height = 300
sprites = ["walkUp.png", "walkDown.png", "walkL.png", "walkR.png"]

for sprite in sprites:
    path = os.path.join("gremlins/agnes-tachyon/sprites", sprite)
    if os.path.exists(path):
        img = QImage(path)
        w, h = img.width(), img.height()
        cols = w // frame_width
        rows = h // frame_height
        print(f"{sprite}: {cols * rows} frames ({cols}x{rows})")
