# Euclid控件库


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.Euclid import *

class EuclidButton(QPushButton):

    def __init__(self, parent=None, text="button", callback=None):
        super().__init__(parent=parent, text=text)
        self.setObjectName(EUCLID_BUTTON)
        if callback != None:
            self.clicked.connect(callback)

    def set_callback(self, callback:callable):
        if callback != None:
            self.clicked.connect(callback)

    def disable(self):
        '''禁用该按钮'''
        self.setEnabled(False)
        restyle(self, EUCLID_BUTTON_DISABLE)

    def enable(self):
        self.setEnabled(True)
        restyle(self, EUCLID_BUTTON)

class EuclidScrollArea(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(EUCLID_SUBAREA)
        self.container = QLabel()
        self.container.setObjectName(EUCLID_SUBAREA_CONTAINER)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.container)

class EuclidRoundPictureBox(QLabel):
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(EUCLID_ROUND_PICTUREBOX)

    def paintEvent(self, evt) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        brush = QBrush(self.pixmap())
        painter.setBrush(brush)
        painter.drawRoundedRect(QPolygon().boundingRect(), 4, 4)
        return super().paintEvent(evt)

class EuclidLineEditor(QLineEdit):
    '''Euclid lineEditor '''

    def __init__(self, focusOutCallback, parent=None):
        '''给定一个函数在编辑器失去聚焦时执行'''

        super().__init__(parent=parent)
        self.setObjectName(EUCLID_LINEEDITOR)
        self.focb = focusOutCallback

    def focusOutEvent(self, event) -> None:
        self.focb()
        return super().focusOutEvent(event)

class EuclidListView(QListWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(EUCLID_LISTVIEW)