"""生成 icon.ico 文件，供 PyInstaller 打包时作为 EXE 图标"""
import sys
import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QFont, QIcon
from PyQt5.QtCore import Qt

def generate():
    app = QApplication(sys.argv)
    
    sizes = [16, 32, 48, 64, 128, 256]
    pixmaps = []
    
    for size in sizes:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        scale = size / 64
        
        painter.setBrush(QBrush(QColor("#007ACC")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(int(4 * scale), int(4 * scale), int(56 * scale), int(56 * scale), int(10 * scale), int(10 * scale))
        
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(int(4 * scale), int(4 * scale), int(56 * scale), int(14 * scale), int(10 * scale), int(10 * scale))
        
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Consolas", max(8, int(22 * scale)), QFont.Bold)
        painter.setFont(font)
        today = str(datetime.date.today().day)
        painter.drawText(pixmap.rect().adjusted(0, int(8 * scale), 0, 0), Qt.AlignCenter, today)
        
        painter.end()
        pixmaps.append(pixmap)
    
    icon = QIcon()
    for pm in pixmaps:
        icon.addPixmap(pm)
    
    pixmaps[-1].save("icon.ico", "ICO")
    print("icon.ico generated successfully.")

if __name__ == '__main__':
    generate()
