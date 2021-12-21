# -*- coding:utf-8 -*-
# /usr/bin/python3
# 基于PyQt5的简易UI系统

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtMultimediaWidgets import *

class EuclidNames:

    EUCLID_WINDOW = "EuclidWindow"
    EUCLID_SIZEGRIP = "EuclidSizeGrip"
    EUCLID_TITLEBAR = "EuclidTitleBar"
    EUCLID_TITLE = "EuclidTitle"
    EUCLID_BUTTON = "EuclidButton"
    EUCLID_MINIBUTTON = "EuclidMiniButton"
    EUCLID_CONTAINER = "EuclidContainer"


class _EuclidMovable:
    '''提供基础的工具让QWidget或者QLabel能够被鼠标直接拖动，而不依赖一个TitleBar
    通常用于无边框的窗体，需要用户绑定一个Widget给它'''

    def __init__(self, widget: QWidget):
        self._can_move = False
        self._start_pos = QPoint()
        self._widget = widget

    def mousePressEvent(self, evt: QMouseEvent) -> None:
        self._can_move = True
        self._start_pos = evt.pos()

    def mouseMoveEvent(self, evt: QMouseEvent) -> None:
        if self._can_move:
            offset = evt.pos() - self._start_pos
            _pos = self._widget.pos()
            self._widget.move(_pos.x() + offset.x(), _pos.y() + offset.y())

    def mouseReleaseEvent(self, evt: QMouseEvent) -> None:
        self._can_move = False
              
class _EuclidSizeGrip(_EuclidMovable):
    '''在让目标Widget可移动的基础之上，允许目标Widget的父类对象被缩放'''

    def __init__(self, widget: QWidget, parentWidget: QWidget):
        _EuclidMovable.__init__(self, widget)
        self.__minsize = parentWidget.minimumSize()
        self.__parent_widget = parentWidget

    def mouseMoveEvent(self, evt: QMouseEvent) -> None:
        if self._can_move:
            offset = evt.pos() - self._start_pos
            _pos = self._widget.pos()
            width, height = self.__parent_widget.width() + offset.x(), self.__parent_widget.height() + offset.y()
            if self.invalidResize(width, height):
                self.__parent_widget.resize(width, height)
                self._widget.move(_pos.x() + offset.x(), _pos.y() + offset.y())

    def invalidResize(self, width, height) -> bool:
        return self.__minsize.width() < width and self.__minsize.height() < height

# =================== Euclid的基础控件集合 =====================
# EuclidMovable
# EuclidSizeGrip
# EuclidButton
# EuclidTitleBar
# EuclidWindow

class EuclidMovable(QLabel):

    def __init__(self, parent=None):
        QLabel.__init__(self, parent=parent)
        self._movable = _EuclidMovable(self)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self._movable.mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self._movable.mouseReleaseEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        self._movable.mouseMoveEvent(a0)

class EuclidSizeGrip(QLabel):
    '''用于缩放EuclidWindow的按钮组件，通常位于EuclidWindow的右下角，该对象必须拥有一个父类对象
    不能单独运行，否则无法产生任何作用'''

    def __init__(self, parent):
        QLabel.__init__(self, parent=parent)
        self.setObjectName(EuclidNames.EUCLID_SIZEGRIP)
        self.resizeButton = _EuclidSizeGrip(self, parent)

    def mousePressEvent(self, evt: QMouseEvent) -> None:
        self.resizeButton.mousePressEvent(evt)

    def mouseMoveEvent(self, evt: QMouseEvent) -> None:
        self.resizeButton.mouseMoveEvent(evt)

    def mouseReleaseEvent(self, evt: QMouseEvent):
        self.resizeButton.mouseReleaseEvent(evt)

class EuclidButton(QPushButton):

    def __init__(self, parent, callback=None):
        QPushButton.__init__(self, parent=parent)
        self.setObjectName(EuclidNames.EUCLID_BUTTON)
        self.has_binded = False
        if callback != None:
            self.has_binded = True
            self.clicked.connect(callback)

    def bind_clicked(self, callback:callable):
        if self.has_binded:
            self.clicked.disconnect()

        if callback is None:
            self.has_binded = False
        else:
            self.clicked.connect(callback)

class EuclidMiniButton(EuclidButton):

    def __init__(self, parent, callback=None):
        EuclidButton.__init__(self, parent, callback)
        self.setObjectName(EuclidNames.EUCLID_MINIBUTTON)

class EuclidTitleBar(QLabel):
    '''EuclidWindow的标题栏, 标题栏必须有一个父类对象'''

    def __init__(self, parent, title="Euclid Window", titleBarHeight=20, closeBtnSize=12, horizontal_padding=5, vertical_padding=0):
        QLabel.__init__(self, parent=parent)
        self.setObjectName(EuclidNames.EUCLID_TITLEBAR)
        self.resize(parent.width(), titleBarHeight)
        self.closebtn_size = min(closeBtnSize, titleBarHeight)

        self.layout = QHBoxLayout(self)
        # title
        self.label = QLabel(self)
        self.label.setObjectName(EuclidNames.EUCLID_TITLE)
        self.label.setText(title)
        self.label.setFixedHeight(titleBarHeight)
        self.layout.addWidget(self.label)

        # close button
        self.button = EuclidMiniButton(self, lambda:parent.hide())
        self.button.setFixedSize(self.closebtn_size, self.closebtn_size)
        self.layout.addWidget(self.button)
        self.layout.setContentsMargins(horizontal_padding, vertical_padding, horizontal_padding, vertical_padding)

    def set_title(self, title:str):
        self.label.setText(title)

    def reset_button_callback(self, callback: callable):
        self.button.bind_clicked(callback)

class EuclidContainer(QLabel):

    def __init__(self, parent=None, padding=5):
        QLabel.__init__(self, parent=parent)
        self.setObjectName(EuclidNames.EUCLID_CONTAINER)
        # self._layout = QVBoxLayout()
        # self._layout.setContentsMargins(padding, padding, padding, padding)
        # self.setLayout(self._layout)

    # def addWidget(self, widget):
    #     self._layout.addWidget(widget)


class EuclidWindow(EuclidMovable):

    def __init__(self, parent=None, title="Euclid Window", width=300, height=300, titleBarHeight=20, minibtn_size=12, hpadding=5, vpadding=0, sizebutton_padding=5):
        EuclidMovable.__init__(self, parent=parent)
        self.setObjectName(EuclidNames.EUCLID_WINDOW)
        self.build(title, width, height, titleBarHeight, minibtn_size, hpadding, vpadding, sizebutton_padding)
        self.__collapsed = False
        self.__size = self.size()

        # 调试代码
        button = EuclidButton(self, callback=lambda:print("hello world"))
        button.setText("测试按钮")
        button.setGeometry(10, self.titleBar.height() + 10, 100, 20)

    def focusInEvent(self, ev: QtGui.QFocusEvent) -> None:
        self.parent().handleTop(self)
        return super().focusInEvent(ev)

    def build(self, title, w, h, titlebar_height, minbtn_size, hp, vp, sizebtn_padding):
        self.resize(w, h)
        
        # title bar
        self.titleBar = EuclidTitleBar(self, title, titlebar_height, minbtn_size, hp, vp)
        self.titleBar.reset_button_callback(self.collapse)

        # resize button
        self.resizeBtn = EuclidSizeGrip(self)
        space = minbtn_size + sizebtn_padding
        self.resizeBtn.setGeometry(self.width() - space, self.height() - space, minbtn_size, minbtn_size)

        # container
        self.container = EuclidContainer(self)
        self.containerHeightSpace = space + titlebar_height
        self.container.setGeometry(0, titlebar_height, self.width(), self.height() - self.containerHeightSpace)
        

    def collapse(self):
        self.__collapsed = not self.__collapsed
        if self.__collapsed:
            self.__size = self.size()
            self.resize(self.titleBar.size())
        else:
            self.resize(self.__size)

    def set_title(self, title:str):
        self.titleBar.set_title(title)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.titleBar.resize(self.width(), self.titleBar.height())
        self.container.resize(self.width(), self.height() - self.containerHeightSpace)


class TestWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self, None)
        self.resize(1000, 600)
        
        self.setStyleSheet('''
            QPushButton#EuclidMiniButton{background:#4da6ff;border-radius:6px;}
            QPushButton#EuclidMiniButton:hover{background:#66ffe3;}
            QPushButton#EuclidMiniButton:pressed{background:#ffffeb;}
            QPushButton#EuclidButton{background:#4da6ff;border-radius:2px;}
            QPushButton#EuclidButton:hover{background:#4b5bab;}
            QPushButton#EuclidButton:pressed{background:#473b78;}
            QLabel#EuclidTitleBar{background:#4b5bab;border-top-left-radius:5px;border-top-right-radius:5px;}
            QLabel#EuclidTitle{color:#ffffeb;}
            QLabel#EuclidSizeGrip{background:#4da6ff;border-radius:6px;}
            QLabel#EuclidWindow{background:rgba(39,39,54,220);border-radius:5px;border: solid 1px #66ffe3;}
        ''')

        self.window = EuclidWindow(parent=self)
        self.window.set_title("播放器")


        self.window1 = EuclidWindow(parent=self)
        self.window1.set_title("测试窗体")

        self.currentTopWindow = self.window1

    def handleTop(self, window):
        self.currentTopWindow.stackUnder(window)
        self.currentTopWindow = window
        



import sys
app = QApplication(sys.argv)
x = TestWidget()
x.show()
exit(app.exec_())