# Name: Euclid
# Author: Biscuit
# Time: 2020-1-3
# Brief: a simple ui widget lib aim to fast build simple editor.
#        the layout of euclid window just like imgui but it based on PyQt5 
#        so it's not dynamic but static 

# ------------------------------------  Euclid Default Style -------------------------------------------

EUCLID_DEFAULT_STYLE = '''
#EuclidBaseWindow{
    /* background-color:#43434f; */
    border-image:url(./res/test.png);
}
#EuclidWindow{
    background-color:rgba(39, 39, 54, 242);
    border-radius:5px;
    border:1px solid grey;
}
#EuclidWindowAlpha{
    background-color:rgba(39, 39, 54, 100);
    border-radius:5px;
    border:1px solid grey;
}
#EuclidContainer{
    background:#4d4d7e;
}
#EuclidContainerHolder{
    border:1px solid grey;
    border-radius:5px;
}
#EuclidContainerHolderNonBorder{

}
#EuclidSizeGrip{
    background-color:#dbd4d4;
    border-radius:6px;
}
#EuclidSizeGrip:hover{
    background-color:#ffffeb;
}
#EuclidTitleBar{
    background-color:#465374;
    border-top-left-radius:5px;
    border-top-right-radius:5px;
    border-right: 1px solid grey;
    border-left: 1px solid grey;
    border-top: 1px solid grey;
}
#EuclidTitleContent{
    color:#ffffeb;
}
#EuclidCloseButton{
    border-radius:6px;
    background-color:#74adbb;
}
#EuclidCloseButton:hover{
    background-color:#acd2db;
}
#EuclidCloseButton:pressed{
    background-color:#c9e5ec;
}
#EuclidLockButtonNormal{
    border-radius:6px;
    background-color:#79be91;
}
#EuclidLockButtonNormal:hover{
    background-color:#a8d8b8;
}
#EuclidLockButtonNormal:pressed{
    background-color:#cff0da;
}
#EuclidLockButtonLocked{
    border-radius:6px;
    background-color:#898989;
}
#EuclidLockButtonLocked:hover{
    background-color:#a9a9a9;
}
#EuclidLockButtonLocked:pressed{
    background-color:#cdcdcd;
}
QScrollArea{
    background:rgba(0, 0, 0, 0);
    border:none;
}
QScrollBar:vertical{
    border:none;
    width:10px;
    border-radius:0px;
    margin:0px 0px 0px 0px;
    background-color:rgba(0,0,0,0);
}
QScrollBar::handle:vertical{
    background-color:#5e5e6c;
    border-radius:5px;
}
QScrollBar::handle:vertical:hover{
    background-color:#43434f;
}
QScrollBar::handle:vertical:pressed{
    background-color:#5e5e6c;
}
QScrollBar::sub-line:vertical{
    border:none;
    height:0px;
    subcontrol-position:top;
    subcontrol-origin:margin;
}
QScrollBar::add-line:vertical{
    border:none;
    height:0px;
    subcontrol-position:bottom;
    subcontrol-origin:margin;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical{
    background:none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical{
    background:none;
}



/* Euclid Base Widgets */

/* button */
#EuclidButton{
    border-radius:2px;
    background-color:#546799;
    color:#ffffeb;
}
#EuclidButton:hover{
    background-color:#5a80a7;
}
#EuclidButton:pressed{
    background-color:#464a73;
}
#EuclidButtonDisable{
    border:none;
    border-radius:2px;
    background-color:grey;
    color:#ffffeb;
}

#EuclidButtonRed{
    border-radius:2px;
    background-color:#9f3847;
    color:#ffffeb;
}
#EuclidButtonRed:hover{
    background-color:#c74446;
}
#EuclidButtonRed:pressed{
    background-color:#6e2731;
}

/* label */
#EuclidLabel{
    border-radius:2px;
    color:#ffffeb;
}
#EuclidLabelError{
    border-radius:2px;
    color:#e22333;
}
#EuclidLabelWarning{
    border-radius:2px;
    color:#fcf660;
}
#EuclidLabelSuccess{
    border-radius:2px;
    color:rgb(0, 255, 0);
}



/* dialog */
#EuclidDialog{
    background-color:rgba(39,39,54,242);
    border-radius:2px;
    border:1px solid grey;
}

/* image */
#EuclidImage{
    background-color:rgba(0,0,0,0);
    border-radius:5px;
    border:1px solid grey;
}
#EuclidImageNonBorder{
    background-color:rgba(0,0,0,0);
    border:none;
}

/* mini indicator */
#EuclidMiniIndicator{
    background-color:#b2d942;
    border-radius:6px;
}
#EuclidMiniIndicatorRun{
    background-color:red;
    border-radius:6px;
}
#EuclidMiniIndicatorInvalid{
    background-color:grey;
    border-radius:6px;
}

/* mini button */
#EuclidMiniButton{
    border-radius:6px;
    background-color:#546799;
}
#EuclidMiniButton:hover{
    background-color:#5a80a7;
}
#EuclidMiniButton:pressed{
    background-color:#464a73;
}

#EuclidMiniButtonRed{
    border-radius:6px;
    background-color:#c74446;
}
#EuclidMiniButtonRed:hover{
    background-color:#e84f51;
}
#EuclidMiniButtonRed:pressed{
    background-color:#9f3847;
}

QComboBox{
   background: rgba(39, 39, 54, 100);
   border:1px solid grey;
   border-radius: 2px;
   color: #ffffeb;
}

QComboBox::drop-down {
   subcontrol-position: center right;
   border-radius:2px;
   border:none;
}
/*QComboBox QAbstractItemView::item {
   padding: 10px 10px 10px 10px;
   background:rgba(39, 39, 54, 100);
}*/
QComboBox QAbstractItemView {
   color: #ffffeb;
   selection-background-color:rgba(39, 39, 54, 100);
   selection-color:#b9f216;
   background: #43434f;
   outline:none;
   border-radius:2px;
}
/*QComboBox QListView::item{
   background: rgba(39, 39, 54, 100);
   min-height:20px;
}*/
'''



from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import hashlib
import json
import os

from matplotlib.pyplot import gray

EUCLID_MINSIZE = (20, 20)

class EuclidGeometry:

    @staticmethod
    def fullsizeGap(gapsize:tuple) -> callable:
        return lambda x:QSize(x.width() - gapsize[0], x.height() - gapsize[1])

    @staticmethod
    def fullsizeGapX(gapx:int) -> callable:
        return lambda x:QSize(x.width() - gapx, x.height())

    @staticmethod
    def fullsizeGapY(gapy:int) -> callable:
        return lambda x:QSize(x.width(), x.height() - gapy)

def fullsize(size):
    return size

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

def store_window_status(baseWindow, windows:list, filepath:str):
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
    o.setdefault("base_window", {
        "size":[baseWindow.width(), baseWindow.height()],
        "pos":[baseWindow.x(), baseWindow.y()]
    })
    o.setdefault("top", EuclidWindow.connectionTop.window_id)
    o.setdefault("window_list", window_list)
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(o, f)

def restore_window_status(baseWindow, filepath:str):
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

            if baseWindow != None:
                window = o["base_window"]
                baseWindow.resize(*window["size"])
                baseWindow.move(*window["pos"])
        except Exception as e:
            print(e)

def next_horizontal_pos(w:QWidget, space:int):
    return w.x() + w.width() + space, w.y()

def next_vertical_pos(w: QWidget, space:int):
    return w.x(), w.y() + w.height() + space


class EuclidNames:

    # euclid base concept
    WINDOW = "EuclidWindow"
    ALPHA_WINDOW = "EuclidWindowAlpha"
    CONTAINER = "EuclidContainer"
    CONTAINER_HOLDER = "EuclidContainerHolder"
    CONTAINER_HOLDER_NONBORDER = "EuclidContainerHolderNonBorder"
    TITLEBAR = "EuclidTitleBar"
    TITLEBAR_CONTENT = "EuclidTitleContent"
    TITLEBAR_CLOSEBTN = "EuclidCloseButton"
    TITLEBAR_LOCKBTN_NORMAL = "EuclidLockButtonNormal"
    TITLEBAR_LOCKBTN_LOCKED = "EuclidLockButtonLocked"
    SIZEGRIP = "EuclidSizeGrip"

    # euclid widgets
    BUTTON = "EuclidButton"
    BUTTON_RED = "EuclidButtonRed"
    BUTTON_DISABLE = "EuclidButtonDisable"

    LABEL = "EuclidLabel"
    LABEL_ERROR = "EuclidLabelError"
    LABEL_WARNING = "EuclidLabelWarning"
    LABEL_SUCCESS = "EuclidLabelSuccess"

    DIALOG = "EuclidDialog"

    MINIINDICATOR = "EuclidMiniIndicator"
    MINIINDICATOR_RUN = "EuclidMiniIndicatorRun"
    MINIINDICATOR_INVALID = "EuclidMiniIndicatorInvalid"

    IMAGE = "EuclidImage"
    IMAGE_NONBORDER = "EuclidImageNonBorder"

    COMBOBOX = "EuclidComboBox"

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

class _EuclidElasticObject:
    ''' if one widget can adjust size, you can provide a 
    size function to compute new size when parent size has changed'''

    def init(self, resizefunc:callable, minsize=None):
        self.setMinimumSize(*(EUCLID_MINSIZE if minsize is None else minsize))
        self.resizefunc = resizefunc
        self.connect(None)

    def __moveto_lt(self, p, s):
        self.move(p, p)

    def __moveto_nexth(self, p, s):
        self.move(*next_horizontal_pos(self.__last, s))

    def __moveto_nextv(self, p, s):
        self.move(*next_vertical_pos(self.__last, s))

    def connect(self, other, h=False):
        '''connect to another object'''

        if other is None:
            self.__last = None
            self.__posfunc = self.__moveto_lt
            return False
        else:
            self.__last = other
            self.__posfunc = self.__moveto_nexth if h else self.__moveto_nextv
            return True

    def repos(self, p, s):
        self.__posfunc(p, s)

    def _resize(self, psize):
        psize = self.resizefunc(psize)
        self.resize(
            max(psize.width(), self.minimumWidth()),
            max(psize.height(), self.minimumHeight())
        )

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
        self.init(resizefunc, minsize=size)

class _EuclidElasticLabel(_EuclidElasticObject, QLabel):
    def __init__(self, resizefunc, size=None, parent=None, **kwargs) -> None:
        super().__init__(parent=parent)
        self.init(resizefunc, minsize=size)

class _EuclidScrollArea(_EuclidElasticObject, QScrollArea):

    def __init__(self, resizefunc, size=None, parent=None, **kwargs) -> None:
        '''the size here means minimum size of current elastic object'''

        super().__init__(parent=parent, **kwargs)
        self.init(resizefunc, minsize=size)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

class EuclidContainer(QWidget):
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

        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.CONTAINER)
        self.__widgets = list()
        self.__padding = padding
        self.__space = space
    
        self.__last = None
        self.__head = None
        self.__minsize = QSize(padding, padding)

    @property
    def eminheight(self):
        return self.__minsize.height()

    @property
    def eminwidth(self):
        return self.__minsize.width()

    def __add(self, w: _EuclidWidget, is_horizontal=False):
        '''add a new EuclidWidget to container, and new widget would as vertical object 
        connected to last object'''

        w.setParent(self)
        self.__widgets.append(w)
        if is_horizontal:
            if not w.connect(self.__last, True):
                self.__head = w
        else:
            if self.__last is None:
                self.__minsize.setHeight(self.__padding + w.minimumHeight())
            else:
                self.__minsize.setHeight(self.__last.y() + self.__last.minimumHeight() + self.__space + w.minimumHeight())
            w.connect(self.__head, False)
            self.__head = w
        self.__last = w
        self.__last.repos(self.__padding, self.__space)
        self.setMinimumHeight(self.__minsize.height())

    def __addcontainer(self, h, resizefunc=None, minsize=None, padding=5, has_border=True):
        if resizefunc is None:
            resizefunc = halfsize
        container = EuclidContainer(padding=padding, space=self.__space)
        holder = _EuclidContainerHolder(container, resizefunc, has_border=has_border, size=minsize)
        if minsize is None:
            minsize = EUCLID_MINSIZE
        holder.setMinimumSize(*minsize)
        self.__add(holder, h)
        return container

    def addcontainerh(self, resizefunc=None, minsize=None, padding=5, has_border=True):
        return self.__addcontainer(True, resizefunc, minsize, padding, has_border)

    def addcontainer(self, resizefunc=None, minsize=None, padding=5, has_border=True):
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
        if ev.button() == Qt.LeftButton:
            self._can_move = True
            self._pos = ev.pos()

    def mouseMoveEvent(self, ev):
        if self._can_move and self._valid:
            move_window(self, ev, self._pos)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
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
    ''' an euclid container must be place in a _EuclidContainerHolder'''

    def __init__(self, container, resizefunc, parent=None, has_border=True, **kwargs):
        super().__init__(resizefunc, parent=parent, **kwargs)
        self.setObjectName(EuclidNames.CONTAINER_HOLDER if has_border else EuclidNames.CONTAINER_HOLDER_NONBORDER)
        self.setWidget(container)
        self.setWidgetResizable(True)
        self._container = container
        self._container.move(0, 0)

    def resizeEvent(self, evt):
        super().resizeEvent(evt)
        self._container.resize(self.height(), self.width())

class EuclidWindow(_EuclidMoveable):
    
    window_list = list()
    topList = list()
    connectionTop = None

    def loadNewWindow(window):
        ''' when create a new window, raise_ target window and
        record to connectionTop'''

        window.window_id = len(EuclidWindow.window_list)
        EuclidWindow.raiseWindow(window)

    def setOnTop(window):
        '''make window always on top'''

        if window not in EuclidWindow.topList:
            window.raise_()
            EuclidWindow.topList.append(window)

    def cancelOnTop(window):
        '''cancel window always on top'''

        if window in EuclidWindow.topList:
            EuclidWindow.topList.remove(window)

    def raiseWindow(window):
        '''raise window as top when window has got focusIn event'''

        if window not in EuclidWindow.topList and window != EuclidWindow.connectionTop:
            window.raise_()
            if len(EuclidWindow.topList) > 0:
                window.stackUnder(EuclidWindow.topList[0])
            EuclidWindow.connectionTop = window

    def __init__(self, contentw=None, parent=None, has_title=True, padding=5, sizegrip_size=12, titlebar_height=20, title="Euclid Window", minsize=(50, 50), **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EuclidNames.WINDOW)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(*minsize)
        self.setFrameStyle(QFrame.NoFrame)

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
        self._container_holder = _EuclidContainerHolder(self._container, fullsize, self, has_border=False)
        self._container_holder.move(0, _titlebar_height)
        self._container_holder_cut = self._sizegrip_offset + _titlebar_height
        contentw.setFocusPolicy(Qt.StrongFocus)
        contentw.installEventFilter(self)
        self.installEventFilter(self)

        self._sizegrip.raise_()

        # window id
        self.window_id = len(EuclidWindow.window_list)
        EuclidWindow.window_list.append(self)
        EuclidWindow.raiseWindow(self)

    def hideSizeGrip(self):
        self._sizegrip.hide()
        self._container_holder_cut -= self._sizegrip_offset

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.FocusIn:
            EuclidWindow.raiseWindow(self)
            return True
        elif event.type() == QEvent.FocusOut:
            return True
        return super().eventFilter(obj, event)

    def add(self, w: _EuclidObject):
        w.setFocusPolicy(Qt.StrongFocus)
        w.installEventFilter(self)
        self._container.add(w)

    def addh(self, w: _EuclidObject):
        w.setFocusPolicy(Qt.StrongFocus)
        w.installEventFilter(self)
        self._container.addh(w)

    def addh_container(self, resizefunc, minsize=None, padding=0, has_border=True):
        c = self._container.addcontainerh(resizefunc, minsize=minsize, padding=padding, has_border=has_border)
        c.installEventFilter(self)
        return c

    def add_container(self, resizefunc, minsize=None, padding=0, has_border=True):
        c = self._container.addcontainer(resizefunc, minsize=minsize, padding=padding, has_border=has_border)
        c.installEventFilter(self)
        return c

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

class EuclidDocker(_EuclidWidget):
    '''contains a unknown QWidget and make it could be layout 
    as a euclidObject '''

    def __init__(self, w=None, size=None):
        super().__init__(size=size)
        self.w = w
        w.setParent(self)

    def set_widget(self, w):
        if self.w != None:
            self.w.setParent(None)
        self.w = w
        self.w.setParent(self)

class EuclidElasticDocker(_EuclidElasticWidget):
    '''can resize self'''

    def __init__(self, resizefunc, w=None, size=None):
        super().__init__(resizefunc, size=size)
        self.w = w
        w.setParent(self)

    def set_widget(self, w):
        if self.w != None:
            self.w.setParent(None)
        self.w = w
        self.w.setParent(self)

    def resizeEvent(self, evt):
        if self.w != None:
            self.w.resize(self.size())

class EuclidLabel(_EuclidLabel):

    def __init__(self, size=(80, 14), text="ulabel", center=False):
        super().__init__(size=size)
        self.setObjectName(EuclidNames.LABEL)
        self.setText(text)
        if center:
            self.setAlignment(Qt.AlignCenter)

    def error(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL_ERROR)

    def warning(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL_WARNING)

    def success(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL_SUCCESS)

    def normal(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL)

class EuclidMiniIndicator(_EuclidLabel):

    def __init__(self):
        super().__init__(size=(12, 12))
        self.setObjectName(EuclidNames.MINIINDICATOR)

    def normal(self):
        restyle(self, EuclidNames.MINIINDICATOR)

    def invalid(self):
        restyle(self, EuclidNames.MINIINDICATOR_INVALID)

    def run(self):
        restyle(self, EuclidNames.MINIINDICATOR_RUN)

class EuclidElasticLabel(_EuclidElasticLabel):

    def __init__(self, resizefunc, size=None, text="ulabel", center=False):
        super().__init__(resizefunc, size=size)
        self.setObjectName(EuclidNames.LABEL)
        self.setText(text)
        if center:
            self.setAlignment(Qt.AlignCenter)

    def error(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL_ERROR)

    def warning(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL_WARNING)

    def success(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL_SUCCESS)

    def normal(self, text:str):
        self.setText(text)
        restyle(self, EuclidNames.LABEL)

class EuclidButton(_EuclidButton):
    ''' universal button'''

    def __init__(self, size=(80, 20), title="ubutton", callback=None):
        super().__init__(size=size)
        self.setObjectName(EuclidNames.BUTTON)
        self.setText(title)
        self.useful = True
        if callback != None:
            self.clicked.connect(callback)

    def set_callback(self, callback:callable):
        self.clicked.connect(callback)

    def invalid(self):
        self.setEnabled(False)
        restyle(self, EuclidNames.BUTTON_DISABLE)

    def resume(self):
        self.setEnabled(True)
        restyle(self, EuclidNames.BUTTON)

class EuclidComboBox(_EuclidElasticObject, QComboBox):

    def __init__(self, resizefunc, size=(80, 20)):
        super().__init__()
        self.setObjectName(EuclidNames.COMBOBOX)
        self.init(resizefunc, size)

    

class EuclidMiniButton(_EuclidMiniButton):

    def __init__(self, callback=None):
        super().__init__(None)
        self.setObjectName(EuclidNames.MINIBUTTON)
        if callback != None:
            self.clicked.connect(callback)

class EuclidDialogBase(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # label content
        self.content = QLabel(self)
        self.content.setObjectName(EuclidNames.DIALOG)
        self.move(QDesktopWidget().availableGeometry().center() - QPoint(self.width() // 2, self.height() // 2))

    def resizeEvent(self, a0):
        self.content.resize(self.width(), self.height())

class EuclidMessageBox(EuclidDialogBase):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.resize(230, 80)
        self._label = EuclidLabel()
        self._label.setParent(self.content)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.move(0, 10)
        self._label.resize(self.width(), self._label.height())

        self._button = EuclidButton(title="确认", callback=self.accept)
        self._button.setParent(self.content)
        self._button.move(75, 34)

    def showMessage(self, content):
        ''' popup a message which need user to confirm '''

        self._label.setText(content)
        self._label.resize(self._label.sizeHint())
        self.exec()

class EuclidImage(_EuclidElasticLabel):
    ''' show image on window '''

    def __init__(self, resizefunc, size=(100, 100), pixmap=None, has_border=False):
        super().__init__(resizefunc, size=size)
        self.setObjectName(EuclidNames.IMAGE if has_border else EuclidNames.IMAGE_NONBORDER)
        self.setAlignment(Qt.AlignCenter)
        if pixmap != None:
            self.setPixmap(pixmap)
        

if __name__ == '__main__':
    pass