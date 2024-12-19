from PySide6.QtCore import QObject, QPoint, qDebug, Qt
from PySide6.QtGui import QPainter, QCursor, QPixmap, QImage
from PySide6.QtQuick import QQuickItem, QQuickPaintedItem
import pathlib

class MousePointer(QQuickPaintedItem):    

    image = QImage("{}/GUI/images/cursor.png".format(pathlib.Path(__file__).parent.resolve()))

    def __init__(self, parent:QQuickItem = None):        
        QQuickPaintedItem.__init__(self, parent)
        self.setImplicitWidth(32)
        self.setImplicitHeight(41)

    def paint(self, painter: QPainter):     
        painter.setRenderHint(QPainter.Antialiasing)        
        painter.drawImage(0, 0, self.image.scaled(self.width(), self.height(), Qt.KeepAspectRatio))

    ###
    # Slots
    #
    def on_nouvelle_position(self, position: QPoint):        
        self.setX(position.x())
        self.setY(position.y())
