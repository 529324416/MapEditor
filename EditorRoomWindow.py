# 房间窗口

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *
from Editor import *


class EditorRoomWindow(EuclidWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent, title="房间库")