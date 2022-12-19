# EuclidSubWindow

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.EuclidLayout import _euclid_area
from Euclid.Euclid import *
import json
import os

def _store_window_status(mainWindow, windows:list, filepath:str):
    '''save all windows' size and positions'''

    o = dict()
    window_list = dict()
    for window in windows:
        cnt = {
            "pos":[window.x(), window.y()],
            "size":[window.width(), window.height()],
            "locked":window._locked,
            "hidden":window.isHidden()
        }
        window_list.setdefault(window.window_id, cnt)
    o.setdefault("base_window", {
        "size":[mainWindow.width(), mainWindow.height()],
        "pos":[mainWindow.x(), mainWindow.y()]
    })
    o.setdefault("top", EuclidWindow.connectionTop.window_id)
    o.setdefault("window_list", window_list)
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(o, f)

def _restore_window_status(mainWindow, filepath:str):
    '''restore all windows' size and positions'''

    if os.path.exists(filepath):
        with open(filepath, "r", encoding='utf-8') as f:
            o = json.load(f)
        
        window_list = o["window_list"]
        for kv in window_list.items():
            try:
                win = EuclidWindow.window_list[int(kv[0])]
                win.move(*kv[1]["pos"])
                win.resize(*kv[1]["size"])
                win.set_lock(kv[1]["locked"])
                if kv[1]["hidden"]:
                    win.hide()
            except:
                pass
        try:
            if mainWindow != None:
                window = o["base_window"]
                mainWindow.resize(*window["size"])
                mainWindow.move(*window["pos"])
        except:
            pass


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
        self.setObjectName(EUCLID_SIZEGRIP)
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

class _EuclidTitleBarBase(QLabel):

    def __init__(self, height, parent, title="Euclid Window", padding=5, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.setObjectName(EUCLID_TITLEBAR)
        self.setFixedHeight(height)
        self.move(QPoint())
        self.padding = padding

        self._title = QLabel(self)
        self._title.setObjectName(EUCLID_TITLEBAR_CONTENT)
        self.set_title(title)

    def set_title(self, text):
        ''' set window title content, and when content has changed
        the label width would change too'''

        self._title.setText(text)
        if len(text) == 0:
            text = EUCLID_WINDOW
        size = self._title.fontMetrics().boundingRect(text).size()
        self._title.resize(size)
        self._title.move(self.padding, int((self.height() - size.height())/2))

class _EuclidTitleBar(_EuclidTitleBarBase):
    '''Euclid Titlt Bar '''

    def __init__(self, height, parent, lockfunc, topfunc, title="Euclid Window", padding=5, btnsize=12, **kwargs):
        super().__init__(height, parent, title=title, padding=padding, **kwargs)

        self._closebtn = _EuclidMiniButton(self, size=(btnsize, btnsize))
        self._closebtn.clicked.connect(lambda:self.parent().hide())
        self._closebtn.setObjectName(EUCLID_TITLEBAR_CLOSEBTN)
        self._closebtn_padding = padding + btnsize

        self._lockbtn = _EuclidMiniButton(self, size=(btnsize, btnsize))
        self._lockbtn.setObjectName(EUCLID_TITLEBAR_LOCKBTN_NORMAL)
        self._lockbtn.clicked.connect(self._lock)
        self._lock_window = lockfunc

        self._topbtn = _EuclidMiniButton(self, size=(btnsize, btnsize))
        self._topbtn.setObjectName(EUCLID_TITLEBAR_LOCKBTN_LOCKED)
        self._topbtn.clicked.connect(self._top)
        self._top_window = topfunc

    def _top(self):
        '''set window on top'''

        if self._top_window():
            restyle(self._topbtn, EUCLID_TITLEBAR_TOPBTN_NORMAL)
        else:
            restyle(self._topbtn, EUCLID_TITLEBAR_LOCKBTN_LOCKED)

    def _lock(self):
        '''lock window and reset style'''

        self.update_lockbtn(self._lock_window())
        
    def update_lockbtn(self, value:bool):
        restyle(self._lockbtn, EUCLID_TITLEBAR_LOCKBTN_LOCKED if value else EUCLID_TITLEBAR_LOCKBTN_NORMAL)

    def resizeEvent(self, ev):
        '''adjust position of closebutton and lockbutton '''
        
        self._closebtn.move(self.width() - self._closebtn_padding, self.padding)
        self._lockbtn.move(self._closebtn.x() - self._closebtn_padding, self.padding)
        self._topbtn.move(self._lockbtn.x() - self._closebtn_padding, self.padding)

class EuclidWindow(_EuclidMoveable):

    window_list = list()
    topList = list()
    connectionTop = None

    def save_layout(mainWindow:QWidget, filepath:str):
        '''保存当前所有子窗体和主窗体的布局信息到指定的文件'''

        _store_window_status(mainWindow, EuclidWindow.window_list, filepath)

    def load_layout(mainWindow:QWidget, filepath:str):
        '''从文件中读取所有子窗体和主窗体的布局信息并实践'''

        _restore_window_status(mainWindow, filepath)

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
        if len(EuclidWindow.topList) > 0:
            window.stackUnder(EuclidWindow.topList[0])

    def raiseWindow(window):
        '''raise window as top when window has got focusIn event'''

        if window not in EuclidWindow.topList and window != EuclidWindow.connectionTop:
            window.raise_()
            if len(EuclidWindow.topList) > 0:
                window.stackUnder(EuclidWindow.topList[0])
            EuclidWindow.connectionTop = window

    def __init__(self, parent=None, padding=5, sizegripSize=12, titleHeight=20, title="Euclid Window", minsize=(100, 100), hasButtons=True, **kwargs):
        super().__init__(parent)
        self.setObjectName(EUCLID_WINDOW)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(*minsize)
        self.setFrameStyle(QFrame.NoFrame)

        # DOC> 缩放按钮和标题栏
        self.padding = padding
        self._sizegrip = _EuclidSizeGrip((sizegripSize, sizegripSize), self)
        self._sizegrip.installEventFilter(self)
        self._sizegrip.setFocusPolicy(Qt.StrongFocus)
        self.sizegripOffset = padding + sizegripSize

        self._locked = False
        self._ontop = False
        self._titlebar_height = titleHeight

        if hasButtons:
            self._titlebar = _EuclidTitleBar(titleHeight, self, self._lock, self._set_top, title=title)
        else:
            self._titlebar = _EuclidTitleBarBase(titleHeight, self, title=title)
        self._titlebar.setFocusPolicy(Qt.StrongFocus)
        self._titlebar.installEventFilter(self)

        # DOC> ScrollArea
        self.contentbar = _euclid_area(parent=self)
        self.contentbar.set_window(self)
        self.contentbar.setFocusPolicy(Qt.StrongFocus)
        self.contentbar.installEventFilter(self)
        self.contentbar.move(0, titleHeight)
        self.contentHeightPadding = self.sizegripOffset + titleHeight

        # DOC> 追加到管理器
        self.window_id = len(EuclidWindow.window_list)
        EuclidWindow.window_list.append(self)
        EuclidWindow.raiseWindow(self)

        self.resize(400, 300)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.FocusIn:
            EuclidWindow.raiseWindow(self)
            self._set_shadow_enabled(True)
            return True
        elif event.type() == QEvent.FocusOut:
            self._set_shadow_enabled(False)
            return True
        return super().eventFilter(obj, event)

    def _set_shadow_enabled(self, value:bool):

        if value:
            effect = QGraphicsDropShadowEffect()
            effect.setOffset(0, 0)
            effect.setBlurRadius(20)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

    def _set_top(self):
        '''set top or unset top '''

        self._ontop = not self._ontop
        if self._ontop:
            EuclidWindow.setOnTop(self)
            return True
        else:
            EuclidWindow.cancelOnTop(self)
            return False

    def _lock(self):
        '''锁定或者解锁当前的窗体/如果窗体已经锁定则解锁,否则锁定'''

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

    def addh(self, widget:QWidget, w=100, h=20, shouldInstallEventFilter=True):
        self.contentbar.addh(widget, w, h, shouldInstallEventFilter)

    def addv(self, widget:QWidget, w=100, h=20, shouldInstallEventFilter=True):
        self.contentbar.addv(widget,w,h, shouldInstallEventFilter)

    def addh_calcw(self, widget:QWidget, w=(0.5,100), h=20, shouldInstallEventFilter=True):
        self.contentbar.addh_calcw(widget, w, h, shouldInstallEventFilter)

    def addh_calch(self, widget:QWidget, w=100, h=(0.5,100), shouldInstallEventFilter=True):
        self.contentbar.addh_calch(widget, w, h, shouldInstallEventFilter)

    def addh_calc(self, widget:QWidget, w=(0.5,100),h=(0.1,20), shouldInstallEventFilter=True):
        self.contentbar.addh_calc(widget, w, h, shouldInstallEventFilter)

    def addv_calcw(self, widget:QWidget, w=(0.5,100), h=20, shouldInstallEventFilter=True):
        self.contentbar.addv_calcw(widget, w, h, shouldInstallEventFilter)

    def addv_calch(self, widget:QWidget, w=100, h=(0.5,100), shouldInstallEventFilter=True):
        self.contentbar.addv_calch(widget, w, h, shouldInstallEventFilter)

    def addv_calc(self, widget:QWidget, w=(0.5,100),h=(0.1,20), shouldInstallEventFilter=True):
        self.contentbar.addv_calc(widget, w, h, shouldInstallEventFilter)

    def addh_area(self, width=100, height=100, **kwargs) -> _euclid_area:
        '''add a new area, the new area will return back for you 
        can add some widget to it'''

        _area = _euclid_area(**kwargs)
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addh(_area, width, height)
        return _area

    def addh_area_calcw(self,width=(0.5,100),height=100) -> _euclid_area:

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addh_calcw(_area, width, height)
        return _area

    def addh_area_calch(self,width=100,height=(0.5,100)) -> _euclid_area:

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addh_calch(_area, width, height)
        return _area

    def addh_area_calc(self,width=(0.5,100),height=(0.5,100)) -> _euclid_area:

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addh_calc(_area, width, height)
        return _area

    def addv_area(self, width=100, height=100) -> _euclid_area:
        '''add a new area, the new area will return back for you 
        can add some widget to it'''

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addv(_area, width, height)
        return _area

    def addv_area_calcw(self,width=(0.5,100),height=100) -> _euclid_area:

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addv_calcw(_area, width, height)
        return _area

    def addv_area_calch(self,width=100,height=(0.5,100)) -> _euclid_area:

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addv_calch(_area, width, height)
        return _area

    def addv_area_calc(self,width=(0.5,100),height=(0.5,100)) -> _euclid_area:

        _area = _euclid_area()
        _area.set_window(self)
        _area.installEventFilter(self)
        self.contentbar.addv_calc(_area, width, height)
        return _area

    def resizeEvent(self, a0):
        self._sizegrip.move(self.width() - self.sizegripOffset, self.height() - self.sizegripOffset)
        self._titlebar.resize(self.width(), self._titlebar.height())
        self.contentbar.resize(self.width(), self.height() - self.contentHeightPadding)


