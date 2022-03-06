# Name: Euclid
# Author: Biscuit
# Time: 2020-1-3
# Brief: a simple ui widget lib aim to fast build simple editor.
#        the layout of euclid window just like imgui but it based on PyQt5 
#        so it's not dynamic but static 

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QScrollArea
from PyQt5.QtCore import QPoint, QSize, Qt
import hashlib
import json
import os

EUCLID_MINSIZE = (100, 100)

def halfsize(size):
    return QSize(
        int(size.width() / 2),
        int(size.height() / 2)
    )

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

def restyle(element: QWidget, name):
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

def next_horizontal_pos(w:QWidget, space:int):
    return w.x() + w.width() + space, w.y()

def next_vertical_pos(w: QWidget, space:int):
    return w.x(), w.y() + w.height() + space


class EuclidNames:

    WINDOW = "EuclidWindow"
    CONTAINER = "EuclidContainer"
    CONTAINER_HOLDER = "EuclidContainerHolder"
    CONTAINER_HOLDER_NONBORDER = "EuclidContainerHolderNonBorder"
    TITLEBAR = "EuclidTitleBar"
    TITLEBAR_CONTENT = "EuclidTitleContent"
    TITLEBAR_CLOSEBTN = "EuclidCloseButton"
    TITLEBAR_LOCKBTN_NORMAL = "EuclidLockButtonNormal"
    TITLEBAR_LOCKBTN_LOCKED = "EuclidLockButtonLocked"
    SIZEGRIP = "EuclidSizeGrip"


    BUTTON = "EuclidButton"

class EucildUtils:

    def clamp(value, _min, _max):
        return max(min(_max, value), _min)

class EuclidError(Exception):

    def __init__(self, message):
        super().__init__()
        self.msg = message

    def __str__(self):
        return self.msg


class _EuclidObject:
    '''_EuclidObject is a fixed object, you can set fixed size when initialized, if no size
    has been given, the size of widget will be treated as fixed size'''

    def init(self, is_fixed=True, size=None):

        self.__last = None
        self.__posfunc = self.__moveto_lt
        if is_fixed:
            if size is None:
                self.setFixedSize(self.size())
            else:
                self.setFixedSize(*size)
        self._current_size = self.minimumSize()

    def __moveto_lt(self, padding, space):
        self.move(padding, padding)

    def __moveto_nexth(self, padding, space):
        self.move(*next_horizontal_pos(self.__last, space))

    def __moveto_nextv(self, padding, space):
        self.move(*next_vertical_pos(self.__last, space))

    def connect(self, other, is_horizontal=False) -> bool:
        '''connect to another _EuclidObject, this would determine the 
        new position of current widget '''

        if other is None:
            self.__last = None
            return False
        else:
            self.__last = other
            self.__posfunc = self.__moveto_nexth if is_horizontal else self.__moveto_nextv
            return True

    def repos(self, padding, space):
        '''reset position of current widget'''
        self.__posfunc(padding, space)

    def _resize(self, psize):
        pass

    def adjust_size(self, size):
        err = size - self._current_size
        self.setFixedSize(size)
        self.parent().something_resized(err)

    def resizeEvent(self, evt):
        # self.parent().somet
        pass

class _EuclidElasticObject(_EuclidObject):
    ''' if one widget can adjust size, you can provide a 
    size function to compute new size when parent size has changed'''

    def init(self, resizefunc:callable, size=None):
        super().init(is_fixed=False)
        self.resizefunc = resizefunc
        if size is None:
            self.setMinimumSize(self.size())
        else:
            self.setMinimumSize(*size)

    def _resize(self, psize):
        self.resize(self.resizefunc(psize))

class _EuclidWidget(_EuclidObject, QWidget):
    def __init__(self, size=None, parent=None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)
        self.init(size=size)

class _EuclidLabel(_EuclidObject, QLabel):
    def __init__(self, size=None, parent=None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)
        self.init(size=size)

class _EuclidButton(_EuclidObject, QPushButton):
    def __init__(self, size=None, parent=None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)
        self.init(size=size)

class _EuclidElasticWidget(_EuclidElasticObject, QWidget):
    def __init__(self, resizefunc, size=None, parent=None, **kwargs) -> None:
        super().__init__(parent=parent)
        self.init(resizefunc, size=size)

class _EuclidElasticLabel(_EuclidElasticObject, QLabel):
    def __init__(self, resizefunc, size=None, parent=None, **kwargs) -> None:
        super().__init__(parent=parent)
        self.init(resizefunc, size=size)

class _EuclidScrollArea(_EuclidElasticObject, QScrollArea):

    def __init__(self, resizefunc, size=None, parent=None, **kwargs) -> None:
        '''the size here means minimum size of current elastic object'''

        super().__init__(parent=parent, **kwargs)
        self.init(resizefunc, size=size)

class EuclidContainer(_EuclidElasticWidget):
    '''represent the layout of euclid, it would hold a group of widgets
    as a container, and itself would also be treated as a EuclidWidget, and it 
    can be add to another EuclidContainer '''

    def __init__(self, space=5, padding=5, parent=None, **kwargs):
        ''' the size of container is determined by the widget which has been added, 
        container will resize as minimum size if container has no space to hold widgets
        otherwise the elastic object would resize as big as possible
        @padding: the first widget to left and to top
        @space: the space to last object
        @size: the fixed size or elastic size'''

        super().__init__(None, size=(padding, padding), parent=parent, **kwargs)
        self.setObjectName(EuclidNames.CONTAINER)
        self.__widgets = list()
        self.__padding = padding
        self.__space = space
    
        self.__last = None
        self.__head = None
        self.__minsize = QSize(padding, padding)

    @property
    def eminheight(self):
        return self.__minsize[1]

    @property
    def eminwidth(self):
        return self.__minsize[0]

    def __add(self, w: _EuclidWidget, is_horizontal=False):
        '''add a new EuclidWidget to container, and new widget would as vertical object 
        connected to last object'''

        w.setParent(self)
        self.__widgets.append(w)
        if is_horizontal:
            if not w.connect(self.__last, True):
                self.__head = w
        else:
            w.connect(self.__head, False)
            self.__head = w
        self.__last = w
        self.__last.repos(self.__padding, self.__space)
        if (minw:=self.__last.x() + self.__last.minimumWidth()) > self.__minsize.width():
            self.__minsize.setWidth(minw)
        if (minh:=self.__last.y() + self.__last.minimumHeight()) > self.__minsize.height():
            self.__minsize.setHeight(minh)
        self.setMinimumSize(self.__minsize)

    def __addcontainer(self, ish, resizefunc=None, minsize=None, padding=5, has_border=True):
        if resizefunc is None:
            resizefunc = halfsize
        container = EuclidContainer(padding=padding, space=self.__space)
        holder = _EuclidContainerHolder(container, resizefunc)
        if minsize is None:
            minsize = EUCLID_MINSIZE
        holder.setMinimumSize(*minsize)
        self.__add(holder, ish)
        return container

    def addcontainerh(self, resizefunc=None, minsize=None, padding=5, has_border=True):
        return self.__addcontainer(True, resizefunc, minsize, padding, has_border)

    def addcontainerv(self, resizefunc=None, minsize=None, padding=5, has_border=True):
        return self.__addcontainer(False, resizefunc, minsize, padding, has_border)

    def something_resized(self, err):
        self.__minsize += err
        self.setMinimumSize(self.__minsize)
        for w in self.__widgets:
            w.repos(self.__padding, self.__space)

    def addh(self, widget: _EuclidWidget):
        self.__add(widget, True)

    def add(self, widget: _EuclidWidget):
        self.__add(widget, False)

    def resizeEvent(self, evt) -> None:
        for w in self.__widgets:
            w._resize(self.size())
        for w in self.__widgets:
            w.repos(self.__padding, self.__space)

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
        restyle(self._lockbtn, EuclidNames.TITLEBAR_LOCKBTN_LOCKED if value else EuclidNames.TITLEBAR_LOCKBTN_NORMAL)

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

class _EuclidContainerHolder(_EuclidScrollArea):

    def __init__(self, container, resizefunc, parent=None, has_border=True, **kwargs):
        super().__init__(resizefunc, parent=parent, **kwargs)
        self.setObjectName(EuclidNames.CONTAINER_HOLDER if has_border else EuclidNames.CONTAINER_HOLDER_NONBORDER)
        self.setWidget(container)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self._container = container
        self._container.move(0, 0)

    def resizeEvent(self, evt):
        self._container.resize(self.height(), self.width())

class EuclidWindow(_EuclidMoveable):
    
    window_list = list()
    top = None

    def __init__(self, contentw=None, parent=None, has_title=True, padding=5, sizegrip_size=12, titlebar_height=20, title="Euclid Window", minsize=(100, 100), **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.WINDOW)
        self.setMinimumSize(*minsize)

        # base attributes
        self.padding = padding

        # about title
        self.has_title = has_title
        _titlebar_height = titlebar_height if has_title else 0
        self._titlebar_height = titlebar_height
        self._titlebar = _EuclidTitleBar(titlebar_height, self, self._lock, title=title)
        if not has_title:
            self._titlebar.hide()

        # about size grip
        self._sizegrip = _EuclidSizeGrip((sizegrip_size, sizegrip_size), self)
        self._sizegrip_offset = padding + sizegrip_size
        self._locked = False

        # about container
        if contentw is None:
            contentw = EuclidContainer(padding=5)
        self._container = contentw
        self._container_holder = _EuclidContainerHolder(self._container, lambda x: x, self, has_border=False)
        self._container_holder.move(0, _titlebar_height)
        self._container_holder_cut = sizegrip_size + padding + _titlebar_height

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
        if self.has_title:self._titlebar.resize(self.width(), self._titlebar.height())
        self._container_holder.resize(self.width(), self.height() - self._container_holder_cut)


# --------------------- 控件库 ------------------------

# class EuclidDebugTool(_EuclidLabel):

#     def __init__(self, size=None, minsize=(100, 100), parent=None):
#         super().__init__(size=size, minsize=minsize, parent=parent)
#         self.setStyleSheet("background:#79be91;")

#     def resizeEvent(self, a0):
#         self.setText(f"({self.width()}, {self.height()})")

class EuclidButton(_EuclidButton):
    ''' universal button'''

    def __init__(self, size=None, title="ubutton", callback=None):
        super().__init__(size=size)
        self.setText(title)
        self.setObjectName(EuclidNames.BUTTON)
        if callback != None:
            self.clicked.connect(callback)

    def set_callback(self, callback:callable):
        self.clicked.connect(callback)

if __name__ == '__main__':
    print(generate_md5("hello world"))