import sys
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect

app = QApplication(sys.argv)
img = QImage("gremlins/gold-ship/sprites/sleep.png")
rect = QRect(0, 0, 350, 350)
frame1 = img.copy(rect)
frame1.save("frame1_test.png")
