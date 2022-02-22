# Name: Euclid
# Author: Biscuit
# Time: 2020-1-3
# Brief: a simple ui widget lib aim to fast build simple editor.
#        the layout of euclid window just like imgui but it based on PyQt5 
#        so it's not dynamic but static 

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import QPoint, QSize


def move_window(window: QWidget, evt, pos: QPoint):
    '''drag window by mouse when mouse is moving
    compute the offset from mouse moving, and add to window 
    @window: a widget
    @evt: QMouseMoveEvent, this function must be called in mouseMoveEvent
    @pos: the position of mouse click '''

    offset = evt.pos() - pos            # get mouse offset
    window.move(window.pos() + offset)
    window.parent().update()

def resize_window(window: QWidget, evt, pos: QPoint):
    '''adjust window size by sizegrip button, button would 
    record the offset of mosue move, and send to window 
    for adjusting size
    @window: target window
    @evt: QMouseMoveEvent
    @pos: the position of mouse click'''

    offset = evt.pos() - pos
    window.resize(window.width() + offset.x(), window.height() + offset.y())
    window.parent().update()


def label_size(label: QLabel):
    ''' compute the size of label '''

    return label.fontMetrics().boundingRect(label.text()).size()


class EuclidNames:

    WINDOW = "EuclidWindow"
    TITLEBAR = "EuclidTitleBar"
    TITLEBAR_CONTENT = "EuclidTitleContent"
    TITLEBAR_CLOSEBTN = "EuclidCloseButton"
    TITLEBAR_LOCKBTN_NORMAL = "EuclidLockButtonNormal"
    TITLEBAR_LOCKBTN_LOCKED = "EuclidLockButtonLocked"
    SIZEGRIP = "EuclidSizeGrip"
    CONTAINER = "EuclidContainer"
    


class EucildUtils:

    def clamp(value, _min, _max):
        return max(min(_max, value), _min)

class _EuclidObject:
    ''' horizontal object would layout self in a horizontal line '''

    def init(self, size: tuple):
        '''size woukd determine that if the widget would resize self
        if size in range from 0 to 1 (include 1), then the value would use as
        percent of parent size, and if size > 1, then the value would use as 
        fixed widget size'''

        self.__size = size
        self.__last = None                          # the last object of this object
        self.__posfunc = None                       # adjust position
        self.__sizefunc = None                      # adjust size

        # set size function according to tuple size
        self.__posfunc = self.__repos_as_head
        if self.__size[0] > 1:
            if self.__size[1] > 1:
                self.__sizefunc = self.__resize_as_fixed
                self.setFixedSize(*size)
            else:
                self.__sizefunc = self.__resize_as_velastic
                self.setFixedWidth(size[0])
        else:
            if self.__size[1] > 1:
                self.__sizefunc = self.__resize_as_helastic
                self.setFixedHeight(size[1])
            else:
                self.__sizefunc = self.__resize_as_elastic

    def connect(self, other, is_horizontal=False):
        '''connect to another _EuclidObject, you can choose if connected as horizontal or 
        vertical by set arguement is_horizontal'''

        self.__last = other
        self.__posfunc = self.__repos_as_horizontal if is_horizontal else self.__repos_as_vertical

    def repos(self, padding):
        '''adjust the position and size of self'''
        self.__sizefunc()
        self.__posfunc(padding)

    def __resize_as_fixed(self):
        pass

    def __resize_as_helastic(self):
        self.resize(int(self.__size[0] * self.parent().width()), self.__size[1])

    def __resize_as_velastic(self):
        self.resize(self.__size[0], int(self.__size[1] * self.parent().height()))

    def __resize_as_elastic(self):
        self.resize(int(self.__size[0] * self.parent().width()), int(self.__size[1] * self.parent().height()))

    def __repos_as_head(self, padding):
        self.move(padding, padding)

    def __repos_as_horizontal(self, padding):
        self.move(self.__last.width() + padding + self.__last.x(), self.__last.y())

    def __repos_as_vertical(self, padding):
        self.move(self.__last.x(), self.__last.height() + padding + self.__last.y())

class EuclidWidget(_EuclidObject, QWidget):
    def __init__(self, size=None, **kwargs) -> None:
        super().__init__(parent=None, **kwargs)
        self.init((self.width(), self.height()) if size == None else size)

class EuclidLabel(_EuclidObject, QLabel):
    def __init__(self, size=None, **kwargs) -> None:
        super().__init__(parent=None, **kwargs)
        self.init((self.width(), self.height()) if size == None else size)

class EuclidButton(_EuclidObject, QPushButton):
    def __init__(self, size=None, **kwargs) -> None:
        super().__init__(parent=None, **kwargs)
        self.init((self.width(), self.height()) if size == None else size)

class EuclidContainer(EuclidWidget):
    '''represent the layout of euclid, it would hold a group of widgets
    as a container, and itself would also be treated as a EuclidWidget, and it 
    can be add to another EuclidContainer'''

    def __init__(self, size=None, padding=5, **kwargs):
        super().__init__(size=size, **kwargs)
        self.__widgets = list()
        self.__horizontal_last = None
        self.__horizontal_head = None
        self.__padding = padding

    def __add(self, widget: EuclidWidget, is_horizontal=False):
        '''add a new EuclidWidget to container, and new widget would as vertical object 
        connected to last object'''

        widget.setParent(self)
        self.__widgets.append(widget)
        if is_horizontal:
            # add a horizontal widget

            if self.__horizontal_head is None:
                # the first widget is added as horizontal

                self.__horizontal_head = widget
                self.__horizontal_last = widget
            else:
                widget.connect(self.__horizontal_last, True)
                self.__horizontal_last = widget   
        else:
            # add a vertical widget
            if self.__horizontal_head is None:
                self.__horizontal_head = widget
                self.__horizontal_last = widget
            else:
                widget.connect(self.__horizontal_head, False)
                self.__horizontal_head = widget
                self.__horizontal_last = widget

    def addh(self, widget: EuclidWidget):
        self.__add(widget, True)

    def add(self, widget: EuclidWidget):
        self.__add(widget, False)

    def resizeEvent(self, evt) -> None:
        for w in self.__widgets:
            w.repos(self.__padding)

class _EuclidMoveable(QLabel):
    '''make widget movable'''

    def __init__(self, parent=None, **kwargs):
        QLabel.__init__(self, parent=parent, **kwargs)
        self._can_move = False

    def mousePressEvent(self, ev):
        self._can_move = True
        self._pos = ev.pos()

    def mouseMoveEvent(self, ev):
        if self._can_move:
            move_window(self, ev, self._pos)

    def mouseReleaseEvent(self, ev):
        self._can_move = False

class _EuclidSizeGrip(_EuclidMoveable):

    def __init__(self, size, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.SIZEGRIP)
        self.setFixedSize(*size)

    def mouseMoveEvent(self, ev):
        '''adjust the size of parent while moving self'''

        if self._can_move:
            resize_window(self.parent(), ev, self._pos)

class _EuclidMiniButton(QPushButton):
    def __init__(self, parent, size=(12, 12), **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setFixedSize(*size)

class _EuclidTitleBar(QLabel):
    '''Euclid Titlt Bar '''

    def __init__(self, height, parent, title="Euclid Window", padding=5, btnsize=12, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.TITLEBAR)
        self.setFixedHeight(height)
        self.move(QPoint())
        self.padding = padding

        self._title = QLabel(self)
        self._title.setObjectName(EuclidNames.TITLEBAR_CONTENT)
        self.set_title(title)

        self._closebtn = _EuclidMiniButton(self, size=(btnsize, btnsize))
        self._closebtn.clicked.connect(lambda:self.parent().hide())
        self._closebtn.setObjectName(EuclidNames.TITLEBAR_CLOSEBTN)
        self._closebtn_padding = padding + btnsize

    def set_title(self, text):
        ''' set window title content, and when content has changed
        the label width would change too'''

        self._title.setText(text)
        if len(text) == 0:
            text = EuclidNames.WINDOW
        size = self._title.fontMetrics().boundingRect(text).size()
        self._title.resize(size)
        self._title.move(self.padding, int((self.height() - size.height())/2))

    def resizeEvent(self, ev):
        '''adjust position of closebutton and lockbutton '''
        self._closebtn.move(self.width() - self._closebtn_padding, self.padding)
    

class EuclidWindow(_EuclidMoveable):

    def __init__(self, parent=None, padding=5, sizegrip_size=12, titlebar_height=20, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self._titlebar = _EuclidTitleBar(titlebar_height, self)
        self._sizegrip = _EuclidSizeGrip((sizegrip_size, sizegrip_size), self)
        self._sizegrip_offset = padding + sizegrip_size
        

    def resizeEvent(self, a0):
        self._sizegrip.move(self.width() - self._sizegrip_offset, self.height() - self._sizegrip_offset)
        self._titlebar.resize(self.width(), self._titlebar.height())