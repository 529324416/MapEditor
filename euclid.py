# Name: Euclid
# Author: Biscuit
# Time: 2020-1-3
# Brief: a simple ui widget lib aim to fast build simple editor.
#        the layout of euclid window just like imgui but it based on PyQt5 
#        so it's not dynamic but static 

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton

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