from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from Euclid.Euclid import *
import math


class Zoom:
    '''用于控制QGraphicsView的缩放'''
    def __init__(self,zoomin_factor=1.25,zoom_clamp=True,zoom_step=1,zoom_range=(5,20)):

        self.zoomin_factor = zoomin_factor
        self.zoomout_factor = 1/zoomin_factor

        self.zoom = 10
        self.zoom_range = zoom_range
        self.zoom_step = zoom_step
        self.zoom_clamp = zoom_clamp
    def compute_zoom_factor(self,value):
        '''根据传递的滚轮数值来计算要缩放的大小'''

        if value > 0:
            if self.zoom < self.zoom_range[1]:
                self.zoom += self.zoom_step
                return self.zoom_clamp,self.zoomin_factor
        else:
            if self.zoom > self.zoom_range[0]:
                self.zoom -= self.zoom_step
                return self.zoom_clamp,self.zoomout_factor
        return False,None

class EuclidSceneGrid(QGraphicsScene):
    '''提供一个用于绘制背景板的场景'''

    def __init__(self,
        ltcolor = QColor("#232323"),
        hvcolor = QColor("#333333"),
        bgcolor = QColor(0,0,0,0),
        size = (32000,32000),
        cellsize = (16, 16),
        lcellsize = 10,
        parent = None):
        ''' 初始化基本的参数,并绘制完整的场景网格线
        @cellsize: 一个小的格子的尺寸
        @lcellsize: 一个大的格子的边长是多少个小格子'''

        super().__init__(parent=parent)
        self.setSceneRect(-size[0]//2, -size[1]//2, size[0], size[1])                   # 设置scene的大小
        self.setBackgroundBrush(bgcolor)                                                # 设置背景笔刷色彩
        self.cellw,self.cellh = cellsize                                                        # 网格尺寸
        self.largeCellW,self.largeCellH = self.cellw * lcellsize, self.cellh * lcellsize
        self.pen_lt = QPen(ltcolor, 0.5)
        self.pen_hv = QPen(hvcolor, 0.8)

    def drawBackground(self,painter,rect):
        '''绘制背景'''
        super().drawBackground(painter,rect)
        lines = list()
        l = int(math.floor(rect.left()))
        r = int(math.ceil(rect.right()))
        t = int(math.floor(rect.top()))
        b = int(math.ceil(rect.bottom()))

        left = l - (l % self.cellw)
        top = t - (t % self.cellh)
        for x in range(left,r,self.cellw):
            lines.append(QLine(x,t,x,b))
        for y in range(top,b,self.cellh):
            lines.append(QLine(l,y,r,y))
        painter.setPen(self.pen_lt)
        painter.drawLines(*lines)

        lines = list()
        left = l - (l % self.largeCellW)
        top = t - (t % self.largeCellH)
        for x in range(left,r,self.largeCellW):
            lines.append(QLine(x,t,x,b))
        for y in range(top,b,self.largeCellH):
            lines.append(QLine(l,y,r,y))
        painter.setPen(self.pen_hv)
        painter.drawLines(*lines)

class EuclidView(QGraphicsView):
    '''视图主要是作为一个存放Scene的容器, 并提供一些基本的导航的功能'''

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(EUCLID_VIEW)
        self.zoom = Zoom()
        self.canMove = False
        self.baseDragMode = QGraphicsView.RubberBandDrag
        self._initialize()

    def _initialize(self):
        '''初始化EuclidView的基本属性'''

        self.setRenderHints(QPainter.Antialiasing|QPainter.HighQualityAntialiasing|QPainter.TextAntialiasing|QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(self.baseDragMode)

    def setBaseRubberBand(self, mode):
        self.baseDragMode = mode
        self.setDragMode(mode)

    def wheelEvent(self, evt):
        show_scale,scale_factor = self.zoom.compute_zoom_factor(evt.angleDelta().y())
        if show_scale:self.scale(scale_factor,scale_factor)

    def mousePressEvent(self,evt: QMouseEvent):
        '''处理鼠标事件'''

        if evt.button() == Qt.LeftButton and evt.modifiers() == Qt.AltModifier:
            self.canMove = True
            self.setDrag(evt)
            return False
        super().mousePressEvent(evt)
        return True

    def mouseReleaseEvent(self,evt):
        '''处理松开鼠标事件'''

        if evt.button() == Qt.LeftButton:
            if self.canMove:
                self.canMove = False
                self.cancelDrag(evt)
                return
        super().mouseReleaseEvent(evt)

    def setDrag(self, evt):
        ''' 设置当前的拖动模式为可以拖动 '''
  
        super().mouseReleaseEvent(QMouseEvent(QEvent.MouseButtonRelease,evt.localPos(),evt.screenPos(),Qt.LeftButton,Qt.NoButton,evt.modifiers()))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(QMouseEvent(evt.type(),evt.localPos(),evt.screenPos(),Qt.LeftButton,evt.buttons()|Qt.LeftButton,evt.modifiers()))

    def cancelDrag(self, evt):
        ''' 取消当前的拖动模式 '''

        super().mouseReleaseEvent(QMouseEvent(evt.type(),evt.localPos(),evt.screenPos(),Qt.LeftButton,evt.buttons()|Qt.LeftButton,evt.modifiers()))
        self.setDragMode(self.baseDragMode)