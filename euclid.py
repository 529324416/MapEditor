# Name: Euclid
# Author: Biscuit
# Time: 2020-1-3
# Brief: a simple ui widget lib aim to fast build simple editor.
#        the layout of euclid window just like imgui but it based on PyQt5 
#        so it's not dynamic but static 

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import QPoint, QSize
import hashlib
import json
import os

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

def set_name(element: QWidget, name):
    '''change the object name of target widget
    and refresh the style'''

    element.setObjectName(name)
    element.style().unpolish(element)
    element.style().polish(element)

def label_size(label: QLabel):
    ''' compute the size of label '''

    return label.fontMetrics().boundingRect(label.text()).size()

def generate_md5(text:str):

    _5 = hashlib.md5()
    _5.update(text.encode())
    return _5.hexdigest()


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
        self._valid = True

    def set_enabled(self, value):
        self._valid = value

    def mousePressEvent(self, ev):
        self._can_move = True
        self._pos = ev.pos()

    def mouseMoveEvent(self, ev):
        if self._can_move and self._valid:
            move_window(self, ev, self._pos)

    def mouseReleaseEvent(self, ev):
        self._can_move = False

class _EuclidSizeGrip(_EuclidMoveable):

    def __init__(self, size, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.SIZEGRIP)
        self.setFixedSize(*size)
        self._valid = True

    def set_enabled(self, value):
        self._valid = value

    def mouseMoveEvent(self, ev):
        '''adjust the size of parent while moving self'''

        if self._can_move and self._valid:
            resize_window(self.parent(), ev, self._pos)

class _EuclidMiniButton(QPushButton):
    def __init__(self, parent, size=(12, 12), **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setFixedSize(*size)

class _EuclidTitleBar(QLabel):
    '''Euclid Titlt Bar '''

    def __init__(self, height, parent, lockfunc, title="Euclid Window", padding=5, btnsize=12, **kwargs):
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

        self._lockbtn = _EuclidMiniButton(self, size=(btnsize, btnsize))
        self._lockbtn.setObjectName(EuclidNames.TITLEBAR_LOCKBTN_NORMAL)
        self._lockbtn.clicked.connect(self._lock)
        self._lock_window = lockfunc

    def _lock(self):
        '''lock window and reset style'''

        self.update_lockbtn(self._lock_window())
        
    def update_lockbtn(self, value:bool):
        set_name(self._lockbtn, EuclidNames.TITLEBAR_LOCKBTN_LOCKED if value else EuclidNames.TITLEBAR_LOCKBTN_NORMAL)

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
        self._lockbtn.move(self._closebtn.x() - self._closebtn_padding, self.padding)

def store_window_status(windows:list, filepath:str):
    '''save all windows' size and positions'''

    o = dict()
    window_list = dict()
    for window in windows:
        cnt = {
            "pos":[window.x(), window.y()],
            "size":[window.width(), window.height()],
            "locked":window.is_locked
        }
        window_list.setdefault(window.window_id, cnt)
    o.setdefault("top", EuclidWindow.top.window_id)
    o.setdefault("window_list", window_list)
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(o, f)

def restore_window_status(filepath:str):
    '''restore all windows' size and positions'''

    if os.path.exists(filepath):
        with open(filepath, "r", encoding='utf-8') as f:
            o = json.load(f)

        try:
            window_list = o["window_list"]
            for kv in window_list.items():
                win = EuclidWindow.window_list[int(kv[0])]
                win.move(*kv[1]["pos"])
                win.resize(*kv[1]["size"])
                win.set_lock(kv[1]["locked"])
        except Exception as e:
            pass

class EuclidWindow(_EuclidMoveable):
    
    window_list = list()
    top = None

    def __init__(self, parent=None, has_title=True, padding=5, sizegrip_size=12, titlebar_height=20, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.WINDOW)

        self.has_title = has_title
        _titlebar_height = titlebar_height if has_title else 0
        self._titlebar_height = titlebar_height
        self._titlebar = _EuclidTitleBar(titlebar_height, self, self._lock)
        if not has_title:
            self._titlebar.hide()
        self._sizegrip = _EuclidSizeGrip((sizegrip_size, sizegrip_size), self)
        self._sizegrip_offset = padding + sizegrip_size
        self._locked = False

        # window id
        self.window_id = len(EuclidWindow.window_list)
        EuclidWindow.window_list.append(self)

        if EuclidWindow.top is None:
            self.raise_()
            EuclidWindow.top = self

    def enable_title(self, value=True):
        '''show or hide title according to value '''

        self.has_title = value
        if value:
            if self._titlebar.isHidden():
                self._titlebar.show()
                self._titlebar.resize(self.width(), self._titlebar_height)
                self._titlebar.setFixedHeight(self._titlebar_height)
        else:
            if not self._titlebar.isHidden():
                self._titlebar.hide()
                self._titlebar.setFixedHeight(0)

    def _lock(self):
        '''lock or unlock window, if window locked, 
        then it cannot be move or resize '''

        self._sizegrip.set_enabled(self._locked)
        self.set_enabled(self._locked)
        self._locked = not self._locked

        # return value to lockbutton
        return self._locked

    def set_lock(self, value:bool) -> None:
        ''' lock or unlock window'''

        self._sizegrip.set_enabled(not value)
        self._titlebar.update_lockbtn(value)
        self.set_enabled(not value)
        self._locked = value

    @property
    def is_locked(self):
        return self._locked

    def resizeEvent(self, a0):
        self._sizegrip.move(self.width() - self._sizegrip_offset, self.height() - self._sizegrip_offset)
        if self.has_title:
            self._titlebar.resize(self.width(), self._titlebar.height())



if __name__ == '__main__':
    print(generate_md5("hello world"))