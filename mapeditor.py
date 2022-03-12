# pyqt5
from difflib import context_diff
from sre_constants import SUCCESS
from tkinter import UNITS
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from matplotlib.pyplot import flag, isinteractive

# euclid
from euclid import *
from euclid import _EuclidLabel, _EuclidElasticWidget, _EuclidElasticLabel, _EuclidScrollArea

# syslibs
import os
import random
import sys
import math
import queue
import time

# other
import numpy as np


def now():

    t = time.localtime()
    return f"{t[3]}:{t[4]}:{t[5]}"

class MsgType:

    NORMAL = 0
    WARNING = 1
    ERROR = 2
    SUCCESS = 3

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
        cellsize = 16,
        lcellsize = 5,
        parent = None):
        ''' 初始化基本的参数,并绘制完整的场景网格线'''

        super().__init__(parent=parent)
        self.setSceneRect(-size[0]//2, -size[1]//2, size[0], size[1])                   # 设置scene的大小
        self.setBackgroundBrush(bgcolor)                                                # 设置背景笔刷色彩
        self.cellsize = cellsize                                                        # 网格尺寸
        self.lcellsize = lcellsize * self.cellsize                                      # 大网格尺寸
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

        left = l - (l % self.cellsize)
        top = t - (t % self.cellsize)
        for x in range(left,r,self.cellsize):
            lines.append(QLine(x,t,x,b))
        for y in range(top,b,self.cellsize):
            lines.append(QLine(l,y,r,y))
        painter.setPen(self.pen_lt)
        painter.drawLines(*lines)

        lines = list()
        left = l - (l % self.lcellsize)
        top = t - (t % self.lcellsize)
        for x in range(left,r,self.lcellsize):
            lines.append(QLine(x,t,x,b))
        for y in range(top,b,self.lcellsize):
            lines.append(QLine(l,y,r,y))
        painter.setPen(self.pen_hv)
        painter.drawLines(*lines)

class EuclidView(QGraphicsView):
    '''视图主要是作为一个存放Scene的容器, 并提供一些基本的导航的功能'''

    def __init__(self,parent=None):
        super().__init__(parent=parent)
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

    def mousePressEvent(self,evt):
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


QSS_INDICATOR = '''
#IndicatorNormal{
    background:rgba(0, 0, 0, 0);
    border:1px solid grey;
    border-radius:2px;
}
#IndicatorNormal:hover{
    border:1px solid #66ffe3;
}


#IndicatorChoozed{
    background:rgba(0, 0, 0, 0);
    border:1px solid red;
    border-radius:2px;
}
#IndicatorTitle{
    color: #ffffeb;
}
'''





# ---------------- 编辑器数据组件 -------------------
# 定义所有该编辑器中需要用的数据对象

MAXSIZE = 64
'''瓦片最大不得超过64'''

UNITSIZE = 8
'''最小的单位是8像素'''


class EditorUtils:
    '''提供一些基础计算工具'''

    def lattice(pos, size):
        '''将一个场景坐标晶格化 '''

        return QPointF(
            (pos.x() // size[0]) * size[0],
            (pos.y() // size[1]) * size[1]
        )

    def latticeUnit(pos):

        return QPointF(
            (pos.x() // UNITSIZE) * UNITSIZE,
            (pos.y() // UNITSIZE) * UNITSIZE
        )

    def cposUnit(pos):
        '''直接将场景坐标转换为网格坐标'''

        return QPoint(int(pos.x() // UNITSIZE), int(pos.y() // UNITSIZE))

    def cposUnit_(pos) -> tuple:
        return int(pos.x() // UNITSIZE), int(pos.y() // UNITSIZE)

    def cpos(pos, size):
        return QPoint(int(pos.x() // size[0]), int(pos.y() // size[1]))

    def spos(pos, size):
        '''将网格坐标转换为晶格化坐标'''

        return QPointF(pos.x() * size[0], pos.y() * size[1])

    def sposUnit(pos: tuple):
        return QPointF(pos[0] * UNITSIZE, pos[1] * UNITSIZE)

class Tile:
    '''瓦片数据, 记录瓦片的数据ID, 文本ID, 图片路径, 复制的路径等所有信息'''

    def __init__(self, name, tileId, filepath):
        self.name = name
        self.tileId = tileId
        self.filepath = filepath
        self.pixmap = QPixmap(filepath)
        self.size = (int(self.pixmap.width()//UNITSIZE), int(self.pixmap.height()//UNITSIZE))
        self.indicatorSize = (self.size[0] * UNITSIZE, self.size[1] * UNITSIZE)
        self.indicatorOffset = (0, self.pixmap.height() - self.indicatorSize[1])
        self.narr = self._toNumpyData()

    @property
    def isUnit(self):
        return self.size == (1, 1)

    def _toNumpyData(self):
        narr = np.full(self.size, -1)
        narr[0, self.size[1] - 1] = self.tileId
        return narr

class TileLut:
    '''瓦片查找表, 也负责导入瓦片, 提供瓦片的数字ID和文本ID的转换渠道'''

    def __init__(self, ID = 1, recycleList=[]):

        self.__ID2TILE = dict()
        self.__NAME2TILE = dict()
        self.ID = ID
        self.recycleList = queue.Queue()
        for value in recycleList:
            self.recycleList.put(value)

        self.createBuffer = list()              # 用于存储上一次加载的所有瓦片

    def toJson(self):
        '''convert value to json '''

        recycleList = []
        while self.recycleList.not_empty:
            recycleList.append(self.recycleList.get())

        return {
            "currentId":self.ID,
            "recycleList":recycleList
        }

    def loadJson(self, o):
        '''从json数据中还原当前的所有数据 '''

    def nextTileId(self):
        '''生成下一个瓦片ID'''

        if self.recycleList.qsize() > 0:
            return self.recycleList.get()
        output = self.ID
        self.ID += 1
        return output

    def __checkFile(self, filepath):
        '''检查目标文件是否有效'''

        # 检查文件路径是否有效
        if os.path.exists(filepath) and os.path.isfile(filepath):
            
            # 检查是否有同名的文件
            if self._nameFromPath(filepath) not in self.__NAME2TILE:
                return True
        return False
            
    def __createTile(self, filepath):
        '''创建一块新的瓦片'''

        if self.__checkFile(filepath):
            tile = Tile(self._nameFromPath(filepath), self.nextTileId(), filepath)
            self.__ID2TILE.setdefault(tile.tileId, tile)
            self.__NAME2TILE.setdefault(tile.name, tile)
            self.createBuffer.append(tile)
            return True
        return False

    def takeBrushFromBuffer(self, brushHandler):
        '''将createBuffer里的所有Tile转换为Brush'''

        return [brushHandler.brushFromRawTile(tile) for tile in self.createBuffer]

    def load(self, files:list) -> int:
        ''' 加载所有的给定的路径, 返回加载失败的数量'''

        err = 0
        self.createBuffer.clear()
        for filepath in files:
            if not self.__createTile(filepath):
                err += 1
        return err

    def _removeTile(self, tile: Tile):
        '''移除一张瓦片, 这次移除不会检查是否可以移除'''

        self.__ID2TILE.pop(tile.tileId)
        self.__NAME2TILE.pop(tile.name)
        self.recycleList.put(tile.tileId)

    def _nameFromPath(self, filepath:str):
        return filepath[filepath.rfind("/") + 1:].replace(".png", "").strip()

    def fetchPixmap(self, tileId):
        return self.__ID2TILE[tileId].pixmap

    def fetch(self, tileId) -> Tile:
        return self.__ID2TILE[tileId]

class BrushMaker:

    def __init__(self, ID = 1):
        '''@ID: 存储当前的笔刷ID'''

        self.ID = ID
        self.recycleList = queue.Queue()

    def nextBrushId(self):

        if self.recycleList.qsize() > 0:
            return self.recycleList.get()
        output = self.ID
        self.ID += 1
        return output

    def brushFromRawTile(self, tile):
        '''根据给定的原始瓦片数据来创建一个笔刷'''

        if tile.isUnit:
            return BrushUnit(self.nextBrushId(), tile)
        return BrushTile(self.nextBrushId(), tile)

    def brushFromRawBrush(self, raw, tilelut: TileLut):
        '''根据调色盘提供的原始笔刷数据来生成一个笔刷'''

        buf = QPixmap(int(raw.rect.width()), int(raw.rect.height()))
        buf.fill(QColor(0, 0, 0, 0))
        painter = QPainter(buf)

        narr = np.full((raw.width, raw.height), -1)
        for tileItem in raw.tiles:
            rawTile = tilelut.fetch(tileItem.tileId)

            # pixmap
            painter.drawPixmap(QRect(
                (tileItem.cx - raw.LB[0]) * UNITSIZE,
                (tileItem.cy - raw.LB[1]) * UNITSIZE - tileItem.heightOffset,
                rawTile.pixmap.width(),
                rawTile.pixmap.height()
            ), rawTile.pixmap)

            # narr
            narr[tileItem.cpos[0] - raw.LB[0], tileItem.cpos[1] - raw.LB[1]] = tileItem.tileId
        return Brush(self.nextBrushId(), raw.tiles, narr, (raw.width, raw.height), buf, raw.LB)


class Tilemap:
    '''存储一张地图的数据信息, 和渲染没有任何关系
    一般用于表示一个绘制图层'''

    def __init__(self, csize=(32, 32)):
        self.data = np.zeros(csize, dtype=np.int8)

    def checkUnit(self, pos: QPoint):
        '''检查目标点位是否可以绘制 '''

        return self.data[pos.x(), pos.y()] == 0

    def erase(self, item):
        '''擦除'''

        self.data[item.cpos[0]: item.cpos[0] + item.size[0], item.cpos[1]: item.cpos[1] + item.size[1]] = np.zeros(item.size)

    def check(self, pos: QPoint, narr:np.ndarray):
        '''检查目标区域是否可以绘制'''

        if pos.x() < 0 or pos.y() < 0:
            return False
        rx, ry = pos.x() + narr.shape[0], pos.y() + narr.shape[1]
        if rx > self.data.shape[0] or ry > self.data.shape[1]:
            return False
        area = self.data[pos.x(): rx, pos.y(): ry]
        return np.all((area * narr) == 0)

    def forceDrawUnit(self, pos, brush):
        '''覆写目标位置的数据'''

        self.data[pos.x(), pos.y()] = brush.tileId

    def forceDraw(self, pos, brush):
        '''复写目标位置的数据'''

        self.data[pos.x(): pos.x() + brush.size[0], pos.y(): pos.y() + brush.size[1]] = brush.narr

    def drawUnit(self, pos, brush):
        '''绘制一个点位'''

        if self.checkUnit(pos):
            self.forceDrawUnit(pos, brush)
            return True
        return False

    def draw(self, pos, brush):
        '''在目标位置绘制笔刷内容'''

        # 检查目标位置是否可以绘制
        if self.check(pos, brush.narr):
            self.forceDraw(pos, brush)
            return True
        return False

    def canMove(self, rawBrush, coffset) -> bool:
        '''检查是否可以将某段数据从一个位置移动到另外一个位置
        1.先将要移动的数据区块设为空, 并保存复原手段
        2.检查目标位置是否可以绘制给定的区块
        3.如果不可以, 则复原, 如果可以, 则执行复制
        
        ## 同时, 如果可以移动的话, 会同时改写rawBrush的LB的位置, 因为默认的选框会
        ## 跟随移动, 于是需要将rawBrush的LB位置增加coffset'''
        try:
        # 将数据清0
        # print(f"{rawBrush.LB},({rawBrush.width},{rawBrush.height}), {coffset}")
            ox, oy = rawBrush.LB[0], rawBrush.LB[1]
            orx, ory = ox + rawBrush.width, oy + rawBrush.height
            self.data[ox: orx, oy: ory] = np.zeros((rawBrush.width, rawBrush.height))

            # 检查目标位置是否可以绘制rawBrush
            x, y = rawBrush.LB[0] + coffset[0], rawBrush.LB[1] + coffset[1]
            rx, ry = x + rawBrush.width, y + rawBrush.height
            area = self.data[x: rx, y: ry]
            if np.all((area * rawBrush.narr) == 0):
                # 可以绘制
                self.data[x: rx, y: ry] = rawBrush.narr
                rawBrush.LB = (x, y)
                return True
            else:
                # 不可以绘制, 还原当前数据状态
                self.data[ox: orx, oy: ory] = rawBrush.narr
                return False
        except Exception as e:
            print(e)
            return False

class BrushUnit:
    ''' 针对一个最小单元点位的笔刷, 由于默认的系统单位点大小是8*8, 所以该
    笔刷用处不是很大 '''

    def __init__(self, Id, tile: Tile):
        ''' @ID: 笔刷的ID信息
            @tile: 笔刷所包含的瓦片信息, 由于该瓦片是点位笔刷, 所以瓦片仅有一张'''

        self.Id = Id
        self.tileId = tile.tileId
        self.pixmap = tile.pixmap
        self.indicator = QGraphicsPixmapItem(self.pixmap)
        self.brushName = "#" + tile.name

    def need(self, tileId):
        return self.tileId == tileId

    def draw(self, pos, tilemap):
        return tilemap.drawUnit(pos)

    def createTile(self, view, cpos):
        return TileItem(view, self.tileId, (cpos.x(), cpos.y()), self.pixmap)

    def __str__(self):
        return self.brushName

class BrushTile:
    '''由一块瓦片构成的笔刷'''

    def __init__(self, Id, tile: Tile):
        '''
        @ID: 笔刷的ID
        @tileIds: 笔刷所含有的所有瓦片的ID
        @narr: 笔刷的numpy数据
        @size: 笔刷的网格大小
        @pixmap: 笔刷的pixmap, 这个pixmap是一个有可能是一个组合pixmap
        @filename: 如果这个笔刷由单个瓦片构成, 那么filename就是瓦片的名称
        '''

        self.Id = Id
        self.tileId = tile.tileId
        self.narr = tile.narr
        self.size = tile.size
        self.pixmap = tile.pixmap
        self.brushName = "#" + tile.name
        self.indicator = QGraphicsPixmapItem(tile.pixmap)
        self.indicatorSize = (tile.size[0] * UNITSIZE, tile.size[1] * UNITSIZE)
        self.indicatorOffset = QPoint(0, tile.pixmap.height() - self.indicatorSize[1])

    def need(self, tileId):
        return self.tileId == tileId

    def draw(self, pos, tilemap: Tilemap):
        return tilemap.draw(pos, self)

    def createTile(self, view, cpos):
        '''创建TileItem'''

        return TileItem(view, self.tileId, (cpos.x(), cpos.y()), self.pixmap)

    def __str__(self):
        return self.brushName

class Brush:
    '''一个由多个瓦片构成的笔刷'''

    def __init__(self, ID:int, tiles:list, narr:np.ndarray, size:tuple, pixmap:QPixmap, LB:tuple):
        '''
        @ID: 笔刷的ID
        @tileIds: 笔刷所含有的所有瓦片的ID
        @narr: 笔刷的numpy数据
        @size: 笔刷的网格大小
        @pixmap: 组合的pixmap, 这是一个指示器
        '''
        
        self.ID = ID
        self.narr = narr
        self.size = size
        self.pixmap = pixmap
        self.brushName = "#" + str(ID)
        self.indicator = QGraphicsPixmapItem(self.pixmap)
        self.indicatorSize = (size[0] * UNITSIZE, size[1] * UNITSIZE)
        self.indicatorOffset = QPointF()

        self.tileIds = set()
        self.posRecord = dict()
        for tileItem in tiles:
            self.tileIds.add(tileItem.tileId)

            # 记录TileItem的坐标位置
            self.posRecord.setdefault((tileItem.cpos[0] - LB[0], tileItem.cpos[1] - LB[1]), (
                tileItem.tileId,
                Editor.tilelut.fetchPixmap(tileItem.tileId)
            ))


    def need(self, tileId):
        '''检查该笔刷是否需要某个瓦片作为基础'''

        return tileId in self.tileIds

    def draw(self, pos, tilemap: Tilemap):
        '''在目标Tilemap绘制当前笔刷内容 '''

        return tilemap.draw(pos, self)

    def createTile(self, view, cpos):

        items = list()
        for _cpos, tile in self.posRecord.items():
            item = TileItem(view, tile[0], (cpos.x() + _cpos[0], cpos.y() + _cpos[1]), tile[1])
            item.setPos(EditorUtils.sposUnit(item.cpos) + QPointF(0, -item.heightOffset))
            items.append(item)
        return items

    def __str__(self):
        return self.brushName

class RawBrush:
    '''原始瓦片数据, 记录一组瓦片, 每张瓦片的位置, 和处于边界位置的瓦片'''

    def __init__(self):

        self.tiles = []
        self.LB = [0, 0]
        self.RT = [0, 0]

    def loadTiles(self, tiles:list):
        self.tiles = tiles
        self.find()
        self._numpy()
        self.rect = QRectF(self.LB[0] * UNITSIZE, self.LB[1] * UNITSIZE, self.width * UNITSIZE, self.height * UNITSIZE)

    def loadTile(self, tile):
        '''仅选中了一块瓦片'''

        self.LB = list(tile.cpos)
        self.width, self.height = tile.size
        self.narr = tile.narr
        self.rect = QRectF(self.LB[0] * UNITSIZE, self.LB[1] * UNITSIZE, self.width * UNITSIZE, self.height * UNITSIZE)

    def find(self):
        '''找到左下角和右上角的位置'''

        _tile = self.tiles[0]
        self.LB = list(_tile.cpos)
        self.RT = [self.LB[0] + _tile.cwidth, self.LB[1] + _tile.cheight]
        for tile in self.tiles[1:]:

            # left and right
            if tile.cx < self.LB[0]:
                self.LB[0] = tile.cx
            elif tile.cx + tile.cwidth > self.RT[0]:
                self.RT[0] = tile.cx + tile.cwidth

            # top and down
            if tile.cy < self.LB[1]:
                self.LB[1] = tile.cy

            elif tile.cy + tile.cheight > self.RT[1]:
                self.RT[1] = tile.cy + tile.cheight

        self.width = self.RT[0] - self.LB[0]
        self.height = self.RT[1] - self.LB[1]

    def _numpy(self):
        '''将给定的一组瓦片转换为numpy数据'''

        self.narr = np.zeros((self.width, self.height))
        for tile in self.tiles:
            _x = tile.cx - self.LB[0]
            _y = tile.cy - self.LB[1]
            self.narr[_x: _x + tile.cwidth, _y: _y + tile.cheight] = tile.narr

class BrushContainer:
    '''一个存储笔刷的容器, 往往会创建多个容器, 用于分组'''

    def __init__(self, name):

        self.name = name
        self.brushList = list()

    def checkTile(self, tile) -> bool:
        '''当要删除一个瓦片的时候, 检查这个组中的笔刷是否需要依赖这个瓦片'''

        for brush in self.brushList:
            if brush.need(tile):
                return True
        return False



























#            ----------- 笔刷窗体 -----------
# 该窗体存放着所有瓦片当前放置的笔刷, 由特殊的容器型控件来维护
# 笔刷窗体分为两个主要控件, 一是笔刷类型, 二是具体的笔刷容器, 每个
# 容器元素都是一个笔刷, 每个笔刷都由一个或者多个瓦片构成


class EditorBrushWindow(EuclidWindow):
    '''笔刷窗体'''

    def __init__(self, tilelut: TileLut, brushMaker: BrushMaker, parent=None):
        super().__init__(parent=parent, title="笔刷库")
        
        # 数据信息
        self.tilelut = tilelut
        self.brushMaker = brushMaker

        # 容器渲染器
        self.brushBoxRenderer = EditorBrushBoxRenderer()
        self.brushBoxList = EditorBrushContainerList(self.tilelut, self.brushMaker, self.brushBoxRenderer)
        self.brushBoxRenderer.callback = self.brushBoxList.onBrushChanged

        self._container.add(self.brushBoxList)
        self._container.addh(self.brushBoxRenderer)

        # 脚手架部分
        self.tilelut.load([
            "./tiles/dt_farm_Tile_1.png",
            "./tiles/testTile.png"
        ])
        for brush in self.tilelut.takeBrushFromBuffer(self.brushMaker):
            self.brushBoxList.tileList.brushList.append(brush)

class EditorBrushContainerList(_EuclidElasticWidget):
    '''笔刷容器列表'''

    def __init__(self, lut: TileLut, brushHandler: BrushMaker, brushContainerRenderer):
        # 所有的笔刷容器列表
        # 每个容器都会有数个笔刷, 笔刷列表可以创建也可以删除, 
        # 唯一不能删除的列表是基础的瓦片列表,每个笔刷都是可以复制和引用的
        # 当要删除这个笔刷时, 则所有的引用都会被删除

        super().__init__(lambda x: QSize(115, x.height() - 30), size=(115, 100))
        self.tileList = BrushContainer("默认瓦片笔刷")
        self.dataList = [self.tileList]
        self.lut = lut
        self.brushMaker = brushHandler
        self.renderer = brushContainerRenderer
        self.setup()
        
        # other
        self.currentList = None
        self.currentBrush = None

    def bindObserver(self, observer):
        self.observer = observer

    def onBrushChanged(self, brush):
        '''重新选择了一个笔刷'''

        if self.observer != None:
            self.observer.showBrush(brush)
        self.currentBrush = brush
        
    def addContainer(self):
        '''添加一组新的笔刷'''

        self.dataList.append(BrushContainer("新建组"))
        self.updateContainerList()

    def openTiles(self):
        '''导入瓦片数据'''

        filenames = QFileDialog.getOpenFileNames(self, "导入瓦片数据", filter="PNG图片文件(*.png)")[0]
        err = self.lut.load(filenames)
        if err > 0:
            print(f"加载完毕, 加载失败数量为{err}")
        
        for brush in self.lut.takeBrushFromBuffer(self.brushMaker):
            self.dataList[0].brushList.append(brush)

        if self.currentList == self.dataList[0]:
            self.renderer.render(self.currentList.brushList)

    def getCurrentList(self):
        '''取得当前可用的组合笔刷组'''

        if self.currentList is None or self.currentList == self.tileList:
            return None
        return self.currentList

    def deleteCurrentGroup(self):
        '''删除当前组'''

        if self.currentList == self.tileList:
            QMessageBox.information(None, "错误报告", "瓦片组不可被删除")
        elif self.currentList is None:
            QMessageBox.information(None, "错误报告", "没有当前组")
        else:
            reply = QMessageBox.question(None, "删除当前组", "是否确认删除?", QMessageBox.Ok|QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.reloadContainerNames()
                self.dataList.remove(self.currentList)
                self.updateContainerList()
                self.currentList = None

    def onItemClicked(self, itemIndex: QModelIndex):
        '''选中目标组'''

        container = self.dataList[itemIndex.row()]
        if self.currentList != container:
            self.currentList = container
            self.renderer.render(container.brushList)
    
    def setup(self):
        self.button = EuclidButton(size=(110, 20), title="添加笔刷组", callback=self.addContainer)
        self.button.move(0, 0)
        self.button.setParent(self)

        self.button2 = EuclidButton(size=(110, 20), title="添加瓦片", callback=self.openTiles)
        self.button2.move(0, 25)
        self.button2.setParent(self)

        self.button3 = EuclidButton(size=(110, 20), title="删除当前组", callback=self.deleteCurrentGroup)
        self.button3.move(0, 50)
        restyle(self.button3, EuclidNames.BUTTON_RED)
        self.button3.setParent(self)

        self.containerList = QListView(self)
        self.containerList.setObjectName("EditorBrushContainerList")
        self.containerList.move(0, 75)
        self.containerList.clicked.connect(self.onItemClicked)
        self.updateContainerList()

    def updateContainerList(self):
        '''更新容器列表名称'''

        model = QStringListModel([container.name for container in self.dataList])
        self.containerList.setModel(model)

    def reloadContainerNames(self):
        '''重新读取所有的组名称'''

        model = self.containerList.model()
        for row in range(model.rowCount()):
            self.dataList[row].name = model.data(model.index(row, 0), 0)

    def resizeEvent(self, evt):
        super().resizeEvent(evt)
        self.containerList.resize(110, self.height() - 75)

class EditorBrushIndicator(QLabel):
    '''单个笔刷渲染器, 展示一张笔刷的图片'''

    def __init__(self, callback, size=(80, 100), parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(QSS_INDICATOR)

        self.pictureBox = QLabel(self)
        self.pictureBox.setAlignment(Qt.AlignCenter)
        self.pictureBox.setFixedSize(size[0], size[1] - 20)
        self.pictureBox.move(0, 0)
        self.pictureBox.setObjectName("IndicatorNormal")

        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFixedSize(size[0], 20)
        self.title.move(0, 80)
        self.title.setObjectName("IndicatorTitle")
        self.callback = callback
        self.brush = None

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        restyle(self.pictureBox, "IndicatorChoozed")
        self.callback(self)

    def showBrush(self, brush):
        pixmap = brush.pixmap
        if pixmap.height() > pixmap.width():
            _pixmap = pixmap.scaledToHeight(self.height())
        else:
            _pixmap = pixmap.scaledToWidth(self.width())
        self.pictureBox.setPixmap(_pixmap)
        self.title.setText(str(brush))
        self.brush = brush

# 笔刷容器渲染器
class EditorBrushBoxRenderer(_EuclidScrollArea):
    '''笔刷容器'''

    def __init__(self, callback=None):
        super().__init__(lambda x:QSize(x.width() - 200, x.height() - 30), size=(100, 100))
        self.setStyleSheet("border:1px solid #3f3f3f;border-radius:2px;")
        self.currentSize = (80, 100)
        self.rowCount = 0
        self.recycleQueue = queue.Queue()
        self.indicators = list()
        self.brushList = list()

        self.container = QWidget()
        self.container.setStyleSheet("border:none;")
        self._layout = QGridLayout(self.container)
        self._layout.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.setWidget(self.container)

        self.currentBrushIndicator = None
        self.callback = callback

    def onBrushChoozed(self, indicator: EditorBrushIndicator):
        '''选中当前的笔刷 '''

        # 本体状态, 调整当前笔刷与子渲染器状态
        if self.currentBrushIndicator != None:
            if self.currentBrushIndicator != indicator:
                restyle(self.currentBrushIndicator.pictureBox, "IndicatorNormal")
        self.currentBrushIndicator = indicator

        # 调整笔刷观察器和调色盘的笔刷内容
        Editor.brushObserver.showBrush(indicator.brush)
        Editor.palette.onBrushChanged(indicator.brush)

    def generate(self):
        '''generate a new indicator'''

        if self.recycleQueue.empty():
            indicator = EditorBrushIndicator(self.onBrushChoozed, size=self.currentSize)
            return indicator
        item = self.recycleQueue.get()
        item.setFixedSize(*self.currentSize)
        item.show()
        return item

    def checkCount(self, count):
        '''保证渲染器的笔刷渲染器数量为count'''

        currentCount = len(self.indicators)
        if currentCount > count:
            for i in range(currentCount - count):
                indicator = self.indicators.pop()
                self._layout.removeWidget(indicator)
                indicator.hide()
                self.recycleQueue.put(indicator)
            return True
        elif currentCount < count:
            for i in range(count - currentCount):
                self.indicators.append(self.generate())
            return True
        return False

    def render(self, brushList:list):
        '''渲染指定的笔刷列表 '''

        self.currentBrushIndicator = None
        self.brushList = brushList
        self.checkCount(len(brushList))
        self.rowCount = self.container.width() // self.currentSize[0]
        for idx, brush in enumerate(brushList):
            self._layout.addWidget(self.indicators[idx], idx//self.rowCount, idx%self.rowCount, 1, 1)
            self.indicators[idx].showBrush(brush)
            restyle(self.indicators[idx].pictureBox, "IndicatorNormal")
        self._updateLayout(len(self.indicators))

    def updateLayoutSize(self):
        '''调整当前网格布局的排布 '''

        count = len(self.indicators)
        rowLength = self.container.width() // self.currentSize[0]
        if rowLength != self.rowCount and count >= rowLength:
            # 横轴长度发生变化, 需要更新所有的渲染器位置

            self.rowCount = rowLength
            self._updateLayout(count)

    def _updateLayout(self, count):
        '''更新容器布局'''

        row = self.rowCount
        for idx, indicator in enumerate(self.indicators):
            self._layout.addWidget(indicator, idx // row, idx % row, 1, 1)
        h = count // row if count % row == 0 else (count // row) + 1
        self.container.setMinimumHeight(h * self.currentSize[1])

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.container.resize(self.width(), max(self.height() - 10, self.container.minimumHeight()))
        self.updateLayoutSize()

# 笔刷观察器
class EditorBrushObserver(EuclidWindow):
    '''显示当前选中的笔刷'''

    def __init__(self, parent=None):
        super().__init__(parent=parent, has_title=False)
        restyle(self, EuclidNames.ALPHA_WINDOW)
        self.pictureBox = EuclidImage(lambda x: QSize(x.width() - 10, x.height() - 30), size=(10, 10), has_border=False)
        self._container.add(self.pictureBox)

        self.title = EuclidElasticLabel(lambda x:QSize(x.width() - 10, 14), size=(10, 14), text="???", center=True)
        self._container.add(self.title)
        self.brush = None

    def showBrush(self, brush):
        pixmap = brush.pixmap
        if pixmap.height() > pixmap.width():
            _pixmap = pixmap.scaledToHeight(self.pictureBox.height())
        else:
            _pixmap = pixmap.scaledToWidth(self.pictureBox.width())
        self.title.setText(str(brush))
        self.pictureBox.setPixmap(_pixmap)
        self.brush = brush

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if self.brush != None:
            self.showBrush(self.brush)






# --------------- 调色盘窗体 -----------------
# 一个既可以绘制, 也可以用来生产笔刷的窗体

class EditorView(EuclidView):

    def __init__(self, enter, leave, move, parent=None):
        super().__init__(parent=parent)
        self.move = move
        self.enter = enter
        self.leave = leave
        self.canEdit = False
        self.canDraw = False

    def setEditable(self, value):
        '''设置当前是否可以编辑调色盘'''

        self.canEdit = value
        self.setBaseRubberBand(QGraphicsView.NoDrag if value else QGraphicsView.RubberBandDrag)

    def mousePressEvent(self, event):
        '''允许执行当前工具'''

        if super().mousePressEvent(event) and self.canEdit:
            if event.button() == Qt.LeftButton:
                self.canDraw = True
                return

    def mouseReleaseEvent(self, event):
        '''停止当前工具'''

        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            self.canDraw = False

    def mouseMoveEvent(self, event):
        '''执行当前工具'''

        super().mouseMoveEvent(event)
        self.move(event, self.canDraw)

    def enterEvent(self, event):
        self.enter(event)

    def leaveEvent(self, event):
        self.canDraw = False
        self.leave(event)

class ITool:
    '''Tool接口, 用于定义Tool的基本行为'''

    def __init__(self, name:str):
        self.name = name

    def onItemPressed(self, item, event):
        pass

    def onItemMove(self, item, event):
        pass

    def onItemReleased(self, item, event):
        pass

    def onSelectionChanged(self):
        pass

    def onMove(self, event, canDraw):
        pass

    def onEnter(self, event):
        pass

    def onLeave(self, event):
        pass

    def done(self):
        pass

class BrushTool(ITool):
    '''笔刷工具, 用于在目标tilemap上绘制内容'''

    def __init__(self, renderer: QGraphicsScene, view, tilemap: Tilemap):
        super().__init__("笔刷")
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.currentBrush = None
        self._enabled = False
        self.view = view
        self.tilemap = tilemap
        self.drawAs = None

    def done(self):
        if self._enabled:
            self.renderer.removeItem(self.currentBrush.indicator)
            self.currentBrush = None
            self._enabled = False

    def setBrush(self, brush: BrushTile):
        '''重设笔刷'''

        if self._enabled:
            # 清理之前的笔刷指示器
            pos = self.currentBrush.indicator.pos()
            self.renderer.removeItem(self.currentBrush.indicator)
            self.currentBrush = brush
            self.renderer.addItem(self.currentBrush.indicator)
            self.currentBrush.indicator.setPos(pos)
        else:
            self._enabled = True
            self.currentBrush = brush
            self.renderer.addItem(self.currentBrush.indicator)
        self.drawAs = self.drawAsCombination if isinstance(self.currentBrush, Brush) else self.drawAsTile

    def clearBrush(self):
        '''移除笔刷'''

        if self._enabled:
            self.renderer.removeItem(self.currentBrush.indicator)
        self._enabled = False
        self.currentBrush = None

    def onEnter(self, event):
        '''当鼠标进入绘制场景'''

        if self._enabled:
            self.currentBrush.indicator.setPos(self.rendererView.mapToScene(event.pos()))

    def drawAsCombination(self, cpos, indicatorPosiiton):
        '''笔刷是一个组合笔刷'''

        items = self.currentBrush.createTile(self.view, cpos)
        for item in items:
            self.renderer.addItem(item)
        return items

    def drawAsTile(self, cpos, indicatorPosition):
        '''笔刷是一个单瓦片笔刷'''

        item = self.currentBrush.createTile(self.view, cpos)
        self.renderer.addItem(item)
        item.setPos(indicatorPosition)
        return item
            
    def onMove(self, event, canDraw):
        '''当鼠标移动时'''

        # 调整笔刷指示器的位置
        if self._enabled:
            pos = self.rendererView.mapToScene(event.pos())
            cpos = EditorUtils.cposUnit(pos)
            indicatorPosition = QPointF(cpos.x() * UNITSIZE, cpos.y() * UNITSIZE) - self.currentBrush.indicatorOffset
            self.currentBrush.indicator.setPos(indicatorPosition)
            if canDraw:
                if self.currentBrush.draw(cpos, self.tilemap):
                    # self.tilemap.recordTile()
                    self.drawAs(cpos, indicatorPosition)

class MarqueeTool(ITool):

    def __init__(self, renderer: QGraphicsScene, tilemap: Tilemap):
        super().__init__("选框")
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.tilemap = tilemap


        # 内部数据
        self.moveTile = False
        self.rawBrush = RawBrush()                                      # 用于生产组合笔刷
        self.rawBrushBorder = QGraphicsRectItem()                       # 组合笔刷边框
        self.rawBrushBorderFlag = False                                 # 记录Border是否存在于场景中, 也可以表示当前是否存在选中的Items
        self.rawBrushBorder.setPen(QPen(QColor("#ff6b97"), 0.7))
        
        self.locationBorder = QGraphicsRectItem()
        self.locationBorderPos = QPointF()
        self.hasLocationBorder = False
        self.locationBorder.setPen(QPen(QColor("#66ffe3"), 0.7))

    def onItemPressed(self, item, event: QGraphicsSceneMouseEvent):
        self.startPos = event.scenePos()
        self.borderPos = self.rawBrushBorder.pos()
        self.moveTile = True

    def onItemMove(self, item, event: QGraphicsSceneMouseEvent):
        if self.moveTile:
            offset = event.scenePos() - self.startPos
            self.rawBrushBorder.setPos(self.borderPos + offset)

            if self.hasLocationBorder:          # 已经构建了定位框, 则直接调整定位框的位置
                coffset = EditorUtils.cposUnit_(offset)
                self.locationBorder.setPos(
                    coffset[0] * UNITSIZE + self.locationBorderPos.x(), 
                    coffset[1] * UNITSIZE + self.locationBorderPos.y()
                )
            else:   # 构建定位选框
                self.hasLocationBorder = True
                self.locationBorder.setRect(self.rawBrushBorder.rect())
                self.locationBorderPos = self.locationBorder.pos()
                self.renderer.addItem(self.locationBorder)

    def onItemReleased(self, item, event: QGraphicsSceneMouseEvent):
        '''移动结束的时候, 如果移动的长度超过了一个最小网格的阈值, 那么重新调整晶格化位置并重设每个移动过的
        TileItem的网格位置参数, 计算方式通过先计算鼠标想要落位的网格位置, 然后以此网格位置为主来计算晶格化偏移
        最后将此偏移应用到所有的对象'''

        self.moveTile = False
        mousePosition = event.scenePos()
        mouseOffset = mousePosition - self.startPos
        if abs(mouseOffset.x()) > 1 or abs(mouseOffset.y()) > 1:
            coffset = EditorUtils.cposUnit_(mouseOffset)

            if coffset != (0, 0):
                # 要移动的点位确定之后, 之后就是解决能不能移动的问题
                if self.tilemap.canMove(self.rawBrush, coffset):
                    # 可以移动, 则开始移动所有的单位

                    for item in self.renderer.selectedItems():
                        item.applyLatticeOffset(coffset)
                    self.borderPos += QPointF(coffset[0] * UNITSIZE, coffset[1] * UNITSIZE)
                    self.rawBrushBorder.setPos(self.borderPos)
                    self.clearLocationBorder()
                    return
        self.resumeRawBrush()
        self.clearLocationBorder()

    def clearLocationBorder(self):
        '''清理定位框'''

        if self.locationBorder.scene() != None:
            self.renderer.removeItem(self.locationBorder)
        self.hasLocationBorder = False

    def resumeRawBrush(self):
        '''移动无效, 所以还原本次移动'''

        for item in self.renderer.selectedItems():
            item.back()
        self.rawBrushBorder.setPos(self.borderPos)
        self.locationBorder.setPos(self.borderPos)

    def onSelectionChanged(self):
        '''当选择元素切换时'''

        try:
            items = self.renderer.selectedItems()
            if len(items) > 0:
                if len(items) > 1:
                    self.rawBrush.loadTiles(items)
                else:
                    self.rawBrush.loadTile(items[0])
                self.borderPos = QPointF()
                self.rawBrushBorder.setPos(self.borderPos)
                self.locationBorder.setPos(self.borderPos)
                self.rawBrushBorder.setRect(self.rawBrush.rect)
                if not self.rawBrushBorderFlag:
                    self.renderer.addItem(self.rawBrushBorder)
                    self.rawBrushBorderFlag = True 
            else:
                self.renderer.removeItem(self.rawBrushBorder)
                self.rawBrushBorderFlag = False
        except Exception as e:
            print(e)

class EraseTool(ITool):

    def __init__(self, renderer: QGraphicsScene, tilemap: Tilemap):
        self.renderer = renderer
        self.rendererView = self.renderer.views()[0]
        self.tilemap = tilemap
        self.indicator = QGraphicsRectItem(0, 0, UNITSIZE, UNITSIZE)
        self.indicator.setPen(QPen(QColor("#ffffeb"), 0.5))
        self.indicator.setFlag(QGraphicsItem.ItemIsPanel)
        self.transform = QTransform()
        self.offset = QPointF(UNITSIZE/2, UNITSIZE/2)
        self._enabled = False

    def work(self):
        self._enabled = True
        self.renderer.addItem(self.indicator)

    def done(self):
        self._enabled = False
        self.renderer.removeItem(self.indicator)

    def onEnter(self, event):
        if self._enabled:
            self.renderer.addItem(self.indicator)
            self.indicator.setPos(self.rendererView.mapToScene(event.pos()))

    def onLeave(self, event):
        if self._enabled:
            self.renderer.removeItem(self.indicator)

    def onMove(self, event, canDraw):
        
        if self._enabled:
            pos = self.rendererView.mapToScene(event.pos()) - self.offset
            self.indicator.setPos(pos)
            if canDraw:
                items = self.renderer.collidingItems(self.indicator, Qt.IntersectsItemBoundingRect)
                for item in items:
                    if isinstance(item, TileItem):
                        self.tilemap.erase(item)
                        self.renderer.removeItem(item)

class EditorTools:
    '''编辑器支持使用的所有编辑工具, 主要是笔刷, 橡皮, 油漆桶, 选框四类'''

    def __init__(self, renderer, palette, tilemap):
        self.brushTool = BrushTool(renderer, palette, tilemap)
        self.marqueeTool = MarqueeTool(renderer, tilemap)
        self.currentTool = self.marqueeTool

class EditorToolType:

    PEN = 0
    MARQUEE = 1
    ERASE = 2

class TileItem(QGraphicsPixmapItem):
    '''代表一个瓦片的渲染实体, 会记录瓦片的ID和位置'''

    def __init__(self, view, tileId, cpos: tuple, pixmap: QPixmap):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsPanel)
        self.view = view

        # 瓦片数据, 和原始瓦片数据类似, 存在Item中是为了方便查询, 以及优化访问速度, 不需要反复访问TileLut
        self.tileId = tileId
        self.cpos = cpos
        self.size = (pixmap.width()//UNITSIZE, pixmap.height()//UNITSIZE)
        self.isUnit = self.size == (1, 1)
        self.heightOffset = pixmap.height() - self.size[1] * UNITSIZE
        self.latticePos = (self.cpos[0] // self.size[0], self.cpos[1] // self.size[1])
        self.lastPos = QPoint(cpos[0] * UNITSIZE, cpos[1] * UNITSIZE - self.heightOffset)
        self.narr = self._toNumpyData()

    @property
    def itemSize(self):
        return (self.size[0] * UNITSIZE, self.size[1] * UNITSIZE)

    def back(self):
        self.setPos(self.lastPos)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self.view.onItemPressed(self, event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self.view.onItemReleased(self, event)

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        self.view.onItemMoved(self, event)

    def applyLatticeOffset(self, offset: tuple):
        '''应用偏移, 重新计算当前的偏移和位置 '''

        self.cpos = (self.cpos[0] + offset[0], self.cpos[1] + offset[1])
        self.latticePos = (self.cpos[0] // self.size[0], self.cpos[1] // self.size[1])
        self.setPos(self.cpos[0] * UNITSIZE, self.cpos[1] * UNITSIZE - self.heightOffset)
        self.lastPos = self.pos()

    def _toNumpyData(self):
        '''转换为numpy的ndarray, 该函数需要检查前缀条件'''

        narr = np.full(self.size, -1)
        narr[0, self.size[1] - 1] = self.tileId
        return narr

    @property
    def cwidth(self):
        return self.size[0]

    @property
    def cheight(self):
        return self.size[1]

    @property
    def cx(self):
        return self.cpos[0]

    @property
    def cy(self):
        return self.cpos[1]

    def paint(self, painter, option, widget):
        option.state = QStyle.State_None
        super().paint(painter, option, widget)

class EditorPalette(EuclidWindow):
    ''' 地图编辑器调色盘 '''

    def __init__(self, tileLut: TileLut, parent=None, paletteCanvasSize=(32, 32)):
        '''初始化功能菜单, 调色盘绘制界面和预览界面'''

        super().__init__(parent=parent, title="调色盘")
        self.renderer = EuclidSceneGrid(ltcolor=QColor("#494949"), hvcolor=QColor("#666666"), cellsize=16, lcellsize=10)
        self.renderer.selectionChanged.connect(self.onSelectionChanged)
        self.renderer_view = EditorView(self.onEnter, self.onLeave, self.onMove)
        self.renderer_view.setScene(self.renderer)
        
        self.tilemapBorder = QGraphicsRectItem(0, 0, paletteCanvasSize[0] * UNITSIZE, paletteCanvasSize[1] * UNITSIZE)
        self.tilemapBorder.setPen(QPen(QColor("#5a80a7")))
        self.renderer.addItem(self.tilemapBorder)
        self.setup()

        self.tileLut = tileLut                              # 瓦片查找表
        self.editable = False                               # 当前是否可以编辑调色盘
        self.tilemap = Tilemap(csize=paletteCanvasSize)     # 调色盘唯一要维护的数据层

        self.currentBrush = None
        self.brushTool = BrushTool(self.renderer, self, self.tilemap)
        self.eraseTool = EraseTool(self.renderer, self.tilemap)
        self.marqueeTool = MarqueeTool(self.renderer, self.tilemap)
        self.currentTool = self.marqueeTool
        self.toolType = EditorToolType.MARQUEE

    def onItemPressed(self, item: TileItem, event: QGraphicsSceneMouseEvent):
        self.currentTool.onItemPressed(item, event)

    def onItemReleased(self, item: TileItem, event: QGraphicsSceneMouseEvent):
        self.currentTool.onItemReleased(item, event)

    def onItemMoved(self, item: TileItem, event: QGraphicsSceneMouseEvent):
        self.currentTool.onItemMove(item, event)

    def onSelectionChanged(self):
        self.currentTool.onSelectionChanged()

    def onEnter(self, event):
        if self.editable:
            self.currentTool.onEnter(event)

    def onLeave(self, event):
        if self.editable:
            self.currentTool.onLeave(event)

    def onMove(self, event, canDraw):
        if self.editable:
            self.currentTool.onMove(event, canDraw)

    def createCombineBrush(self):
        '''创建组合笔刷'''

        if self.currentTool != self.marqueeTool:
            self.output("请先进入选择模式", 1)
        elif len(self.renderer.selectedItems()) < 2:
            self.output("组合笔刷至少是两块瓦片", 2)
        else:
            '''可以创建'''
            brushList = Editor.brushList.getCurrentList()
            if brushList is None:
                self.output("请选择一个非默认的笔刷组", 2)
            else:
                brushList.brushList.append(Editor.brushMaker.brushFromRawBrush(self.marqueeTool.rawBrush, self.tileLut))

    def resetItemFlags(self, flags):

        items = self.renderer.items()
        for item in items:
            if isinstance(item, TileItem):
                item.setFlags(flags)

    def convertTool(self, toolType):
        '''转换当前的工具类型'''

        if toolType == self.toolType:
            return

        self.currentTool.done()
        self.toolType = toolType
        if toolType == EditorToolType.PEN:
            self.editable = True
            self.renderer_view.setEditable(True)
            self.statusLabel.setText("编辑调色盘")
            self.statusIndicator.run()
            if self.currentBrush != None:
                self.brushTool.setBrush(self.currentBrush)
            self.currentTool = self.brushTool
            self.infobar.normal("编辑中..")
            self.resetItemFlags(QGraphicsItem.ItemIsPanel)

        elif toolType == EditorToolType.MARQUEE:
            self.editable = False
            self.renderer_view.setEditable(False)
            self.statusLabel.setText("笔刷选择")
            self.statusIndicator.normal()
            self.currentTool = self.marqueeTool
            self.infobar.normal("调色盘进入选择模式")
            self.resetItemFlags(QGraphicsItem.ItemIsMovable|QGraphicsItem.ItemIsSelectable)

        elif toolType == EditorToolType.ERASE:
            self.editable = True
            self.renderer_view.setEditable(True)
            self.statusLabel.setText("编辑调色盘")
            self.statusIndicator.run()
            self.currentTool = self.eraseTool
            self.eraseTool.work()
            self.infobar.normal("编辑中..")
            self.resetItemFlags(QGraphicsItem.ItemIsPanel)

    def onBrushChanged(self, brush):
        '''笔刷被重设'''

        self.currentBrush = brush
        if self.editable and self.toolType == EditorToolType.PEN:
            self.brushTool.setBrush(brush)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Escape:
            self.convertTool(EditorToolType.MARQUEE)
        elif event.key() == Qt.Key_B:
            self.convertTool(EditorToolType.PEN)
        elif event.key() == Qt.Key_E:
            self.convertTool(EditorToolType.ERASE)
        

    def debug(self):
        '''显示当前的地图数据'''

        print(self.tilemap.data.transpose(1, 0))

    def debug2(self):
        for k, v in self.tilemap.tiles.items():
            print(k, v)

    def output(self, message, type=MsgType.NORMAL):

        if type == MsgType.NORMAL:
            self.infobar.normal(f"{now()} {message}")
        elif type == MsgType.WARNING:
            self.infobar.warning(f"{now()} {message}")
        elif type == MsgType.ERROR:
            self.infobar.error(f"{now()} {message}")
        elif type == MsgType.SUCCESS:
            self.infobar.success(f"{now()} {message}")
        else:
            self.infobar.normal(f"{now()} {message}")

    def setup(self):
        '''将所有的控件安排到容器中'''
        
        self.statusIndicator = EuclidMiniIndicator()
        self._container.add(self.statusIndicator)
        self.statusLabel = EuclidLabel(text="笔刷选择")
        self._container.addh(self.statusLabel)

        self.splitter = EuclidLabel(size=(14, 14), text="|")
        self._container.addh(self.splitter)

        self.infobar = EuclidElasticLabel(lambda x: QSize(x.width() - 100, 14), (100, 14), text="")
        self._container.addh(self.infobar)
        self.infobar.success("..")


        _func = lambda x: QSize(x.width() - 10, max(x.height() - 100, 100))
        self._container.add(EuclidElasticDocker(_func, self.renderer_view, size=(100, 100)))
        
        self.editBtn = EuclidButton(title="编辑调色盘", callback=lambda:self.convertTool(EditorToolType.PEN), size=(120, 20))
        self._container.add(self.editBtn)

        self.createBrushBtn = EuclidButton(title="创建组合笔刷", callback=self.createCombineBrush)
        self._container.addh(self.createBrushBtn)

        self.debugBtn = EuclidButton(title="测试", callback=self.debug)
        self._container.addh(self.debugBtn)





class Editor:
    '''编辑器所有主要单元'''

    tilelut = TileLut()                             # 瓦片查找表
    brushMaker = BrushMaker()                       # 笔刷生成器
    
    # 需要创建的所有窗体单元
    palette = None                                  # 调色盘
    brushObserver = None                            # 笔刷观察器
    brushWindow = None


    # 其他子单元
    brushContainer = None                           # 笔刷组渲染器
    brushList = None                                # 笔刷组列表

    @staticmethod
    def create(parent=None):

        Editor.palette = EditorPalette(Editor.tilelut, parent=parent, paletteCanvasSize=(8, 8))
        Editor.brushObserver = EditorBrushObserver(parent=parent)
        Editor.brushWindow = EditorBrushWindow(Editor.tilelut, Editor.brushMaker, parent=parent)

        Editor.brushContainer = Editor.brushWindow.brushBoxRenderer
        Editor.brushList = Editor.brushWindow.brushBoxList


class Window(QLabel):

    def __init__(self):
        super().__init__(None)
        self.setObjectName("EuclidBaseWindow")
        self.resize(int(1308*0.8), int(1120*0.8))
        self.build()
        self.show()

    def build(self):
        
        Editor.create(self)
        restore_window_status(self, "./res/test.json")

    def test(self):
        dialog = EuclidMessageBox()
        dialog.exec()

    def closeEvent(self, a0):
        store_window_status(self, EuclidWindow.window_list, "./res/test.json")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("zpix", 9)
    font.setStyleStrategy(QFont.NoAntialias)
    app.setFont(font)
    with open("./res/style.qss", encoding='utf-8') as f:
        qss = f.read()
    with open("editorstyle.qss", encoding='utf-8') as f:
        app.setStyleSheet(f"{qss}\n{f.read()}")
    window = Window()
    exit(app.exec_())