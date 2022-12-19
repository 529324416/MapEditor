# 将Euclid中的C函数重新封装为一个给定的PyQt布局

from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets import QLabel, QScrollArea, QWidget
from PyQt5.QtGui import QMouseEvent

from Euclid import _euclid
from Euclid.Euclid import *


class _euclid_direction:
    HORIZONTAL = 0x0
    VERTICAL = 0x2

class _euclid_container(QLabel):
    '''euclid container, hold other widgets, and it also can 
    place a sub container in'''

    def __init__(self, parent=None, std_capacity=10, space=10, entry_point=(10, 10), size=(1000, 600)):
        super().__init__(parent=parent)
        self.setObjectName(EUCLID_CONTAINER)
        self.__container = _euclid._create_container(std_capacity, space, entry_point, size)
        self.__children = list()
        self.resize(*size)

    def _add(self, widget: QWidget, elem:object, direction:int):
        '''add a widget with a element to describe it'''

        widget.setParent(self)
        self.__children.append(widget)
        _euclid.add(self.__container, elem, direction)
        self.update()

    def eu_resize(self, size):
        _euclid.resize(self.__container, size)
        self.resize(*_euclid._container_minsize(self.__container))
        for idx, widget in enumerate(self.__children):
            widget.setGeometry(*_euclid._elem_rect(self.__container, idx))


class _euclid_area(QScrollArea):

    def __init__(self, parent=None, std_capacity=10, spacing=10, entry_point=(10, 10), std_size=(100,100)):
        super().__init__(parent)
        self.setObjectName(EUCLID_AREA)
        self.container = _euclid_container(std_capacity=std_capacity, space=spacing, entry_point=entry_point, size=std_size)
        self.setWidget(self.container)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container.eu_resize((0, 0))
        self.window = None

    def set_window(self, parent):
        if parent != None:
            self.window = parent

    def addh(self, widget:QWidget, width=100, height=20, shouldFilterEvent=True):
        '''add a new widget to this area, 
        it will stay in horizontal next to last element'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elem(width, height)
        self.container._add(widget, _elem, _euclid_direction.HORIZONTAL)

    def addv(self, widget:QWidget, width=100, height=20, shouldFilterEvent=True):
        '''add a new widget to this area, 
        it will stay in vertical next to last element'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elem(width, height)
        self.container._add(widget, _elem, _euclid_direction.VERTICAL)

    def addh_calcw(self, widget:QWidget, width=(0.5,100), height=20, shouldFilterEvent=True):
        '''add a new widget to this area, the widget would both has 
        ratio part and constant part in width'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elemcalcw(width, height)
        self.container._add(widget, _elem, _euclid_direction.HORIZONTAL)

    def addv_calcw(self, widget:QWidget, width=(0.5,100), height=20, shouldFilterEvent=True):
        '''add a new widget to this area, the widget would both has 
        ratio part and constant part in width'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elemcalcw(width, height)
        self.container._add(widget, _elem, _euclid_direction.VERTICAL)

    def addh_calch(self, widget:QWidget, width=100, height=(0.1, 20), shouldFilterEvent=True):
        '''add a new widget to this area, the widget would both has 
        ratio part and constant part in height'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elemcalch(width, height)
        self.container._add(widget, _elem, _euclid_direction.HORIZONTAL)

    def addv_calch(self, widget:QWidget, width=100, height=(0.1, 20), shouldFilterEvent=True):
        '''add a new widget to this area, the widget would both has 
        ratio part and constant part in height'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elemcalch(width, height)
        self.container._add(widget, _elem, _euclid_direction.VERTICAL)

    def addh_calc(self, widget:QWidget, width=(0.5,100), height=(0.5,100), shouldFilterEvent=True):
        '''add a new widget to this area, the widget would has both 
        ratio part and constant part in width and height'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elemcalc(width, height)
        self.container._add(widget, _elem, _euclid_direction.HORIZONTAL)

    def addv_calc(self, widget:QWidget, width=(0.5,100), height=(0.5,100), shouldFilterEvent=True):
        '''add a new widget to this area, the widget would has both 
        ratio part and constant part in width and height'''

        if shouldFilterEvent and self.window != None:
            widget.installEventFilter(self.window)
        _elem = _euclid._create_elemcalc(width, height)
        self.container._add(widget, _elem, _euclid_direction.VERTICAL)

    def resizeEvent(self, evt) -> None:
        super().resizeEvent(evt)
        self.container.eu_resize((self.width(), self.height()))
    