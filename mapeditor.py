# pyqt5

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# euclid
from euclid import *
from euclid import _EuclidElasticWidget, _EuclidScrollArea
from editorSupport import *

# syslibs
import os
import sys
import math
import time
import queue
import shutil
import zipfile
import collections

# other
import numpy as np

EDITOR_VERSION = "0.90_AlphaTest"

def now():

    t = time.localtime()
    return f"{t[3]}:{t[4]}:{t[5]}"

def removeFolder(folder:str, clear=True):
    '''删除文件夹下所有的文件'''

    for file in os.listdir(folder):
        path = f"{folder}/{file}"
        if os.path.isfile(path):
            os.remove(path)
        else:
            removeFolder(path, True)
    if clear:
        os.rmdir(folder)

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

UNITCSIZE = (1, 1)
UNITSIZE = 8
'''最小的单位是8像素'''

LAST = -9999


class EditorUtils:
    '''提供一些基础计算工具'''

    def pixmapCSize_(pixmap: QPixmap) -> tuple:
        return int(pixmap.width()//UNITSIZE), int(pixmap.height()//UNITSIZE)

    def rectSize(p1, p2) -> tuple:
        return abs(p1.x() - p2.x()), abs(p1.y() - p2.y())

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

    def sposUnit_(pos: tuple):
        return QPointF(pos[0] * UNITSIZE, pos[1] * UNITSIZE)

    def sposUnit(pos: QPoint):
        return QPointF(pos.x() * UNITSIZE, pos.y() * UNITSIZE)

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

    def __init__(self):

        self.IdToTile = {}
        self.nameToTile = {}
        self.IdToPixmap = {}

    def loadFromLut(self, lut:dict, folder="./tmp"):
        '''加载瓦片查找表数据'''

        try:
            nameToId = lut["nameToId"]
            self.IdToTile = {}
            self.nameToTile = {}
            self.IdToPixmap = {}                # 优化搜索pixmap的速度

            for name in lut["filenames"]:
                Id = nameToId[name]
                tile = Tile(name, Id, f"{folder}/pictures/{name}.png")
                self.nameToTile.setdefault(name, tile)
                self.IdToTile.setdefault(Id, tile)
                self.IdToPixmap.setdefault(Id, tile.pixmap)
            return True
        except Exception as e:
            return False

    def generateBrushes(self) -> list:
        '''生成所有的瓦片笔刷'''

        Editor.brushMaker.clear()
        brushList = list()
        for tile in self.IdToTile.values():
            brushList.append(Editor.brushMaker.brushFromRawTile(tile))
        return brushList
        
    def fetchPixmap(self, tileId):
        return self.IdToPixmap[tileId]

    def fetch(self, tileId) -> Tile:
        return self.IdToTile[tileId]

    def hasTile(self, tileId:int) -> bool:
        return tileId in self.IdToTile

    def exportAsJson(self):
        '''导出一份json文件, 仅用作转换名称与ID'''

        o = dict()
        for name, tile in self.nameToTile.items():
            o.setdefault(name, tile.tileId)
        return o

    # def toJson(self):
    #     '''convert value to json '''

    #     recycleList = []
    #     while self.recycleList.not_empty:
    #         recycleList.append(self.recycleList.get())

    #     return {
    #         "currentId":self.ID,
    #         "recycleList":recycleList
    #     }

    # def nextTileId(self):
    #     '''生成下一个瓦片ID'''

    #     if self.recycleList.qsize() > 0:
    #         return self.recycleList.get()
    #     output = self.ID
    #     self.ID += 1
    #     return output

    # def __checkFile(self, filepath):
    #     '''检查目标文件是否有效'''

    #     # 检查文件路径是否有效
    #     if os.path.exists(filepath) and os.path.isfile(filepath):
            
    #         # 检查是否有同名的文件
    #         if self._nameFromPath(filepath) not in self.__NAME2TILE:
    #             return True
    #     return False
            
    # def __createTile(self, filepath):
    #     '''创建一块新的瓦片'''

    #     if self.__checkFile(filepath):
    #         tile = Tile(self._nameFromPath(filepath), self.nextTileId(), filepath)
    #         self.__ID2TILE.setdefault(tile.tileId, tile)
    #         self.__NAME2TILE.setdefault(tile.name, tile)
    #         self.createBuffer.append(tile)
    #         return True
    #     return False

    # def takeBrushFromBuffer(self, brushHandler):
    #     '''将createBuffer里的所有Tile转换为Brush'''

    #     return [brushHandler.brushFromRawTile(tile) for tile in self.createBuffer]

    # def load(self, files:list) -> int:
    #     ''' 加载所有的给定的路径, 返回加载失败的数量'''

    #     err = 0
    #     self.createBuffer.clear()
    #     for filepath in files:
    #         if not self.__createTile(filepath):
    #             err += 1
    #     return err

    # def _removeTile(self, tileId: Tile):
    #     '''移除一张瓦片, 这次移除不会检查是否可以移除'''

    #     tile = self.__ID2TILE.pop(tileId)
    #     self.__NAME2TILE.pop(tile.name)
    #     self.recycleList.put(tile.tileId)

    # def _nameFromPath(self, filepath:str):
    #     return filepath[filepath.rfind("/") + 1:].replace(".png", "").strip()

class BrushMaker:

    def __init__(self, ID = 1):
        '''@ID: 存储当前的笔刷ID'''

        self.ID = ID
        self.recycleList = queue.Queue()

    def clear(self):
        '''清空之前的创建信息'''

        while self.recycleList.qsize() > 0:
            self.recycleList.get()
        self.ID = 1

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

    def makeCombineBrushData(self, raw) -> tuple:
        '''根据原始笔刷数据来创建一个组合笔刷的指示器与对应的numpy数据
        以及所用到的瓦片ID组合与所有瓦片的位置记录'''

        narr = np.full((raw.width, raw.height), 0)
        buf = QPixmap(int(raw.rect.width()), int(raw.rect.height()))
        buf.fill(Editor.ALPHA)
        tileIds = set()
        posRecord = dict()
        painter = QPainter(buf)
        for tileItem in raw.tiles:
            tileIds.add(tileItem.tileId)
            tileInfo = Editor.tilelut.fetch(tileItem.tileId)            # 获取瓦片信息
            x, y = tileItem.cx - raw.LB[0], tileItem.cy - raw.LB[1]     # 获取当前Item的局部位置
            pix = tileInfo.pixmap
            painter.drawPixmap(x * UNITSIZE, y * UNITSIZE + int(tileItem.offset.y()), pix.width(), pix.height(), pix)
            narr[x: x + tileInfo.size[0], y: y + tileInfo.size[1]] = tileInfo.narr
            posRecord.setdefault((x, y), tileItem.tileId)
        return buf, narr, tileIds, posRecord

    def makeCombineBrushDataFromJson(self, o:dict) -> tuple:
        '''根据保存的json数据来创建一个组合笔刷的指示器与对应的numpy数据'''

        size = o["size"]
        narr = np.full(size, 0)
        buf = QPixmap(int(size[0] * UNITSIZE), int(size[1] * UNITSIZE))
        buf.fill(Editor.ALPHA)
        tileIds = set()
        posRecord = dict()
        painter = QPainter(buf)
        for info in o["tiles"]:
            pos, tileId = info["pos"], info["tile"]
            tileIds.add(tileId)
            tileInfo = Editor.tilelut.fetch(tileId)
            x, y = pos[0], pos[1]
            pix = tileInfo.pixmap
            painter.drawPixmap(x * UNITSIZE, y * UNITSIZE - tileInfo.indicatorOffset[1], pix.width(), pix.height(), pix)
            narr[x: x + tileInfo.size[0], y: y + tileInfo.size[1]] = tileInfo.narr
            posRecord.setdefault((x, y), tileId)
        return buf, narr, tileIds, posRecord

    def brushFromRawBrush(self, raw):
        '''根据调色盘提供的原始笔刷数据来生成一个笔刷'''

        brush = Brush(self.nextBrushId())
        brush.initFromRawBrush(raw)
        return brush

    def brushFromJson(self, o:dict) -> bool:
        '''从json数据中恢复一个笔刷, 调用该函数前确保瓦片查找表有效'''

        if o["type"] == BRUSH_TYPE.UNIT:
            return self._unitBrushFromJson(o)
        elif o["type"] == BRUSH_TYPE.TILE:
            return self._tileBrushFromJson(o)
        elif o["type"] == BRUSH_TYPE.COMBINE:
            return self._combineBrushFromJson(o)
        return None

    def _combineBrushFromJson(self, o:dict) -> bool:
        '''从json数据中恢复一个组合笔刷'''

        brush = Brush(o["id"])
        brush.initFromJson(o)
        return brush

    def _tileBrushFromJson(self, o:dict):
        '''从json数据中恢复一个瓦片笔刷'''
        return BrushTile(o["id"], Editor.tilelut.fetch(o["tileId"]))

    def _unitBrushFromJson(self, o:dict):
        '''从json数据中恢复一个单元瓦片笔刷'''
        return BrushUnit(o["id"], Editor.tilelut.fetch(o["tileId"]))

class Tilemap:
    '''存储一张地图的数据信息, 和渲染没有任何关系
    一般用于表示一个绘制图层'''

    def __init__(self, csize=(32, 32)):
        self.data = np.zeros(csize, dtype=np.int8)
        self.size = csize
        self.hasSaved = True

    def clone(self):
        '''克隆出一个当前的副本'''

        t = Tilemap(self.size)
        t.data = np.copy(self.data)
        return t

    def show(self):
        print(self.data.transpose(1, 0))

    def save(self, filepath):
        '''保存当前地图的数据'''
        self.hasSaved = True

    def checkUnit(self, pos: QPoint):
        '''检查目标点位是否可以绘制 '''

        return self.data[pos.x(), pos.y()] == 0

    def erase(self, item):
        '''擦除'''

        self.data[item.cpos[0]: item.cpos[0] + item.size[0], item.cpos[1]: item.cpos[1] + item.size[1]] = np.zeros(item.size)
        self.hasSaved = False

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
        self.hasSaved = False

    def forceDraw(self, pos, narr):
        '''复写目标位置的数据'''

        self.data[pos.x(): pos.x() + narr.shape[0], pos.y(): pos.y() + narr.shape[1]] = narr
        self.hasSaved = False

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
            self.forceDraw(pos, brush.narr)
            return True
        return False

    def drawRaw(self, pos:QPoint, narr:np.ndarray) -> bool:
        '''检查是否可以复制,如果可以则写入数据'''

        if self.check(pos, narr):
            self.forceDraw(pos, narr)
            return True
        return False

    def floodFill(self, brush, cpos) -> set:
        '''洪水填充算法'''

        if self.check(cpos, brush.narr):
            pool = set([(cpos.x(), cpos.y())])
            self.posesAround((cpos.x(), cpos.y()), brush.size, pool, brush.narr)
            for p in pool:
                self.data[p[0]:p[0] + brush.size[0],  p[1]:p[1] + brush.size[1]] = brush.narr
            return pool
        return set()

    def posesAround(self, p, s, pool, narr) -> list:
        '''获取当前点周围的4个点
        @p: 给定的目标单位
        @s: 目标笔刷的大小 '''

        l = p[0] - s[0], p[1]
        if self.checkPosForFloodFill(l, s, narr, pool):
            pool.add(l)
            self.posesAroundExceptRight(l, s, pool, narr)

        r = p[0] + s[0], p[1]
        if self.checkPosForFloodFill(r, s, narr, pool):
            pool.add(r)
            self.posesAroundExceptLeft(r, s, pool, narr)

        b = p[0], p[1] - s[1]
        if self.checkPosForFloodFill(b, s, narr, pool):
            pool.add(b)
            self.posesAroundExceptTop(b, s, pool, narr)

        t = p[0], p[1] + s[1]
        if self.checkPosForFloodFill(t, s, narr, pool):
            pool.add(t)
            self.posesAroundExceptBottom(t, s, pool, narr)

    def posesAroundExceptLeft(self, p, s, pool, narr):
        '''获取当前点周围的除了左侧点的三个点'''

        r = p[0] + s[0], p[1]
        if self.checkPosForFloodFill(r, s, narr, pool):
            pool.add(r)
            self.posesAroundExceptLeft(r, s, pool, narr)

        b = p[0], p[1] - s[1]
        if self.checkPosForFloodFill(b, s, narr, pool):
            pool.add(b)
            self.posesAroundExceptTop(b, s, pool, narr)

        t = p[0], p[1] + s[1]
        if self.checkPosForFloodFill(t, s, narr, pool):
            pool.add(t)
            self.posesAroundExceptBottom(t, s, pool, narr)

    def posesAroundExceptRight(self, p, s, pool, narr):
        '''获取当前点周围的除了右侧点的三个点'''

        l = p[0] - s[0], p[1]
        if self.checkPosForFloodFill(l, s, narr, pool):
            pool.add(l)
            self.posesAroundExceptRight(l, s, pool, narr)

        b = p[0], p[1] - s[1]
        if self.checkPosForFloodFill(b, s, narr, pool):
            pool.add(b)
            self.posesAroundExceptTop(b, s, pool, narr)

        t = p[0], p[1] + s[1]
        if self.checkPosForFloodFill(t, s, narr, pool):
            pool.add(t)
            self.posesAroundExceptBottom(t, s, pool, narr)

    def posesAroundExceptTop(self, p, s, pool, narr):
        '''获取当前点周围的除了上侧点的三个点'''

        l = p[0] - s[0], p[1]
        if self.checkPosForFloodFill(l, s, narr, pool):
            pool.add(l)
            self.posesAroundExceptRight(l, s, pool, narr)

        r = p[0] + s[0], p[1]
        if self.checkPosForFloodFill(r, s, narr, pool):
            pool.add(r)
            self.posesAroundExceptLeft(r, s, pool, narr)

        b = p[0], p[1] - s[1]
        if self.checkPosForFloodFill(b, s, narr, pool):
            pool.add(b)
            self.posesAroundExceptTop(b, s, pool, narr)

    def posesAroundExceptBottom(self, p, s, pool, narr):
        '''获取当前点周围的除了下侧点的三个点'''

        l = p[0] - s[0], p[1]
        if self.checkPosForFloodFill(l, s, narr, pool):
            pool.add(l)
            self.posesAroundExceptRight(l, s, pool, narr)

        r = p[0] + s[0], p[1]
        if self.checkPosForFloodFill(r, s, narr, pool):
            pool.add(r)
            self.posesAroundExceptLeft(r, s, pool, narr)

        t = p[0], p[1] + s[1]
        if self.checkPosForFloodFill(t, s, narr, pool):
            pool.add(t)
            self.posesAroundExceptBottom(t, s, pool, narr)

    def checkPosForFloodFill(self, p, s, narr, pool):
        '''检查目标点位是否有效, 超出当前tilemap的范围即为无效位置
        同时, 如果位置有效, 则检查目标位置是否已经填充了数据'''

        if p in pool:
            return False
        if p[0] < 0 or p[1] < 0:
            return False
        ox, oy = p[0] + s[0], p[1] + s[1]
        if ox > self.size[0] or oy > self.size[1]:
            return False
        # 检查目标位置是否可以填入给定的数据
        area = self.data[p[0]: ox, p[1]: oy]
        return np.all((area * narr) == 0)

    def canMove(self, rawBrush, coffset) -> bool:
        '''检查是否可以将某段数据从一个位置移动到另外一个位置
        1.先将要移动的数据区块设为空, 并保存复原手段
        2.检查目标位置是否可以绘制给定的区块
        3.如果不可以, 则复原, 如果可以, 则执行复制
        
        ## 同时, 如果可以移动的话, 会同时改写rawBrush的LB的位置, 因为默认的选框会
        ## 跟随移动, 于是需要将rawBrush的LB位置增加coffset'''

        x, y = rawBrush.LB[0] + coffset[0], rawBrush.LB[1] + coffset[1]
        rx, ry = x + rawBrush.width, y + rawBrush.height
        if x < 0 or y < 0:
            return
        if rx > self.size[0] or ry > self.size[1]:
            return

        # 优先检查目标位置是否有效
        ox, oy = rawBrush.LB[0], rawBrush.LB[1]
        orx, ory = ox + rawBrush.width, oy + rawBrush.height
        self.data[ox: orx, oy: ory] = np.zeros((rawBrush.width, rawBrush.height))

        # 检查目标位置是否可以绘制rawBrush

        area = self.data[x: rx, y: ry]
        if np.all((area * rawBrush.narr) == 0):
            # 可以绘制
            self.data[x: rx, y: ry] = rawBrush.narr
            rawBrush.LB = (x, y)
            self.hasSaved = False
            return True
        else:
            # 不可以绘制, 还原当前数据状态
            self.data[ox: orx, oy: ory] = rawBrush.narr
            return False

class BRUSH_TYPE:
    '''笔刷的三种类型'''

    UNIT = 0
    TILE = 1
    COMBINE = 2

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
        self.indicatorRoom = QGraphicsPixmapItem(self.pixmap)
        self.brushName = "#" + str(Id)
        self.size = UNITCSIZE
        self.narr = np.full(self.size, self.Id)

    def toJson(self):
        '''转换为json数据'''

        return {"type": BRUSH_TYPE.UNIT, "id": self.Id, "tileId":self.tileId}

    def need(self, tileId):
        return self.tileId == tileId

    def draw(self, pos, tilemap):
        return tilemap.drawUnit(pos)

    def createTile(self, view, cpos):
        return TileItem(view, self.tileId, (cpos.x(), cpos.y()), self.pixmap)

    def createRoomTile(self, view, cpos):
        return RoomTileItem(view, self.tileId, (cpos.x(), cpos.y()), self.pixmap)

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
        self.brushName = "#" + str(Id)
        self.indicator = QGraphicsPixmapItem(tile.pixmap)
        self.indicatorSize = (tile.size[0] * UNITSIZE, tile.size[1] * UNITSIZE)
        self.indicatorOffset = QPoint(0, tile.pixmap.height() - self.indicatorSize[1])
        self.indicatorRoom = QGraphicsPixmapItem(tile.pixmap)

    def toJson(self):
        '''转换为Json数据'''

        return {"type":BRUSH_TYPE.TILE, "id":self.Id, "tileId":self.tileId}

    def need(self, tileId):
        return self.tileId == tileId

    def draw(self, pos, tilemap: Tilemap):
        return tilemap.draw(pos, self)

    def createTile(self, view, cpos):
        '''创建TileItem'''

        return TileItem(view, self.tileId, (cpos.x(), cpos.y()), self.pixmap)

    def createRoomTile(self, view, cpos):
        '''创建房间瓦片'''

        return RoomTileItem(view, self.tileId, (cpos.x(), cpos.y()), self.pixmap)

    def __str__(self):
        return self.brushName

class Brush:
    '''一个由多个瓦片构成的笔刷'''

    def __init__(self, Id:int):
        '''@ID: 笔刷的ID'''
        
        self.Id = Id

    def initFromRawBrush(self, raw):
        '''根据选框数据来初始化当前笔刷
        @raw: 原始笔刷数据(即选框数据)'''

        self.size = (raw.width, raw.height)                                                                     # 获取当前的网格大小
        self.pixmap, self.narr, self.tileIds, self.posRecord = Editor.brushMaker.makeCombineBrushData(raw)      # 获取组合指示器与numpy数据
        self.init()

    def initFromJson(self, o:dict):
        '''从JSON数据中恢复当前的笔刷'''

        self.size = o["size"]               # 获取大小
        self.pixmap, self.narr, self.tileIds, self.posRecord = Editor.brushMaker.makeCombineBrushDataFromJson(o)
        self.init()

    def init(self):
        '''通用初始化'''
        self.indicator = QGraphicsPixmapItem(self.pixmap)
        self.indicatorRoom = QGraphicsPixmapItem(self.pixmap)
        self.indicatorSize = (self.size[0] * UNITSIZE, self.size[1] * UNITSIZE)
        self.indicatorOffset = QPointF()

    def toJson(self):
        '''转换为json数据'''

        tiles = list()
        for pos, value in self.posRecord.items():
            tiles.append({"pos":pos, "tile":value})
        return {
            "type":BRUSH_TYPE.COMBINE,              # 组合笔刷
            "id":self.Id,
            "size":self.size,
            "tiles":tiles
        }

    def need(self, tileId):
        '''检查该笔刷是否需要某个瓦片作为基础'''

        return tileId in self.tileIds

    def draw(self, pos, tilemap: Tilemap):
        '''在目标Tilemap绘制当前笔刷内容 '''

        return tilemap.draw(pos, self)

    def createTile(self, view, cpos):
        '''创建一组瓦片, 主要用于调色盘中'''

        items = list()
        for _cpos, tile in self.posRecord.items():
            item = TileItem(view, tile, (cpos.x() + _cpos[0], cpos.y() + _cpos[1]), Editor.tilelut.fetchPixmap(tile))
            item.repos()
            items.append(item)
        return items

    def createRoomTile(self, view, cpos, entryPoint):
        '''创建一组瓦片, 增加房间位置偏移 '''

        items = list()
        roomOffset = entryPoint * UNITSIZE
        for _cpos, tile in self.posRecord.items():
            item = RoomTileItem(view, tile, (cpos.x() + _cpos[0], cpos.y() + _cpos[1]), Editor.tilelut.fetchPixmap(tile))
            item.reposOffset(roomOffset)
            items.append(item)
        return items

    def __str__(self):
        return "#" + str(self.Id)

class RawBrushCopy:
    '''RawBrush的数据副本'''

    def __init__(self, size:tuple, narr:np.ndarray, tiles:list, LB:tuple):
        self.size = size
        self.narr = np.copy(narr)
        self.tiles = [tile.clone() for tile in tiles]
        for tile in self.tiles:
            tile.cpos = (tile.cpos[0] - LB[0], tile.cpos[1] - LB[1])

class RawBrush:
    '''原始瓦片数据, 记录一组瓦片, 每张瓦片的位置, 和处于边界位置的瓦片'''

    def __init__(self):

        self.tiles = []
        self.LB = [0, 0]
        self.RT = [0, 0]

    def clone(self):
        '''复制一份当前地数据'''

        return RawBrushCopy((self.width, self.height), self.narr, self.tiles, self.LB)

    def loadTiles(self, tiles:list):
        self.tiles = tiles
        self.find()
        self._numpy()
        self.rect = QRectF(0, 0, self.width * UNITSIZE, self.height * UNITSIZE)

    def loadTile(self, tile):
        '''仅选中了一块瓦片'''

        self.tiles = [tile]
        self.LB = list(tile.cpos)
        self.width, self.height = tile.size
        self.narr = tile.narr
        self.rect = QRectF(0, 0, self.width * UNITSIZE, self.height * UNITSIZE)

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

    def hasBrush(self, brush:Brush) -> bool:
        '''检查目标容器中是否已经有了brush'''
        return brush in self.brushList

    def appendBrush(self, brush: Brush) -> bool:
        if self.hasBrush(brush):
            return False
        self.brushList.append(brush)
        return True

    def toJson(self) -> dict:
        '''转换为json数据'''

        return {"name":self.name, "brushList":[brush.toJson() for brush in self.brushList]}

    def fromJson(self, o:dict):
        '''清空当前的数据并从json数据中还原所有的信息'''

        self.name = o["name"]
        self.brushList.clear()
        for brush in o["brushList"]:
            self.brushList.append(Editor.brushMaker.brushFromJson(brush))
















#            ----------- 笔刷窗体 -----------
# 该窗体存放着所有瓦片当前放置的笔刷, 由特殊的容器型控件来维护
# 笔刷窗体分为两个主要控件, 一是笔刷类型, 二是具体的笔刷容器, 每个
# 容器元素都是一个笔刷, 每个笔刷都由一个或者多个瓦片构成


class EditorBrushWindow(EuclidWindow):
    '''笔刷窗体'''

    def __init__(self, parent=None):
        super().__init__(parent=parent, title="笔刷库")

        # 容器渲染器
        self.brushBoxRenderer = EditorBrushBoxRenderer()
        self.brushBoxList = EditorBrushContainerList(self.brushBoxRenderer)
        self.add(self.brushBoxList)
        self.addh(self.brushBoxRenderer)

        # 容器渲染器功能按键
        c = self.addh_container(lambda x:QSize(70, x.height() - 30), has_border=False)
        self.removeTileBtn = EuclidButton(title="删除笔刷", size=(60, 20), callback=self.removeCurrentBrush)
        c.add(self.removeTileBtn)


        # 脚手架部分
        # self.tilelut.load([
        #     "./tiles/dt_farm_Tile_1.png",
        #     "./tiles/testTile.png"
        # ])
        # for brush in self.tilelut.takeBrushFromBuffer(self.brushMaker):
        #     self.brushBoxList.tileLib.brushList.append(brush)

    def toJson(self):
        '''将除了瓦片笔刷之外的所有笔刷都转换为json数据'''
        return self.brushBoxList.toJson()

    def fromJson(self, o):
        '''从json数据中恢复当前的笔刷库'''
        self.brushBoxList.fromJson(o)

    def loadTileBrushes(self, brushList):
        '''加载所有的瓦片笔刷'''

        # 先清空之前的笔刷信息
        self.brushBoxList.tileLib.brushList.clear()
        for brush in brushList:
            self.brushBoxList.tileLib.appendBrush(brush)
        self.brushBoxRenderer.reload()

    def invalid(self):
        '''禁用当前笔刷窗体的控件'''

        self.brushBoxList.button.invalid()
        self.removeTileBtn.invalid()

    def resume(self):
        '''恢复当前笔刷窗体的控件'''

        self.brushBoxList.button.resume()
        self.removeTileBtn.resume()

    def removeCurrentBrush(self):
        '''移除当前选中的笔刷'''

        if self.brushBoxRenderer.currentBrushIndicator is None:
            warning("删除笔刷", "当前没有选中的笔刷")
        else:
            brush = self.brushBoxRenderer.currentBrushIndicator.brush
            if isinstance(brush, Brush):
                '''如果不是瓦片, 则直接删除'''
                self.brushBoxRenderer.currentBrushList.remove(brush)
                self.brushBoxRenderer.reload()
                Editor.onBrushClear()
            else:
                # 如果目标是一个瓦片的话, 需要确保该笔刷并不是瓦片库的笔刷
                _container = Editor.brushList.currentContainer
                if _container.name != Editor.brushList.tileLibName:
                    # 当前笔刷可以直接删除
                    _container.brushList.remove(brush)
                    self.brushBoxRenderer.reload()
                    Editor.onBrushClear()
                # else:
                #     # 如果是瓦片库的笔刷，则说明要删除一块瓦片，这需要先确保这块瓦片已经不被任何单位占用
                #     if Editor.removeTile(brush.tileId):
                #         # 瓦片删除成功，删除当前的瓦片笔刷
                #         self.brushBoxList.tileLib.brushList.remove(brush)
                #         self.brushBoxRenderer.reload()

class EditorBrushContainerList(_EuclidElasticWidget):
    '''笔刷容器列表'''

    def __init__(self, brushContainerRenderer, tileListName="瓦片库"):
        # 所有的笔刷容器列表
        # 每个容器都会有数个笔刷, 笔刷列表可以创建也可以删除, 
        # 唯一不能删除的列表是基础的瓦片列表,每个笔刷都是可以复制和引用的
        # 当要删除这个笔刷时, 则所有的引用都会被删除

        super().__init__(lambda x: QSize(115, x.height() - 30), size=(115, 100))
        self.brushContainerNames = [tileListName]
        self.tileLibName = tileListName
        self.tileLib = BrushContainer(tileListName)
        self.brushContainerDatas = {tileListName:self.tileLib}
        self.renderer = brushContainerRenderer
        self.setup()
        self.containerList.add(tileListName)
        
        # other
        self.currentContainer = None

    def toJson(self):
        '''将除了瓦片库之外的所有笔刷都转换为json数据'''

        output = list()
        for name, container in self.brushContainerDatas.items():
            if name != self.tileLibName:
                output.append(container.toJson())
        return output

    def fromJson(self, o:list):
        '''从json数据中恢复当前的笔刷库列表, 这个操作将会清空当前的所有数据, 执行该函数之前先确保
        瓦片库已经加载了'''

        # 写入数据
        self.brushContainerDatas.clear()
        self.brushContainerNames.clear()
        self.brushContainerNames.append(self.tileLibName)
        self.brushContainerDatas.setdefault(self.tileLibName, self.tileLib)
        for brushContainer in o:
            container = BrushContainer("tmp")
            container.fromJson(brushContainer)
            self.brushContainerDatas.setdefault(container.name, container)
            self.brushContainerNames.append(container.name)

        # 更新渲染
        self.containerList.clear()
        for name in self.brushContainerNames:
            self.containerList.add(name)

    # def openTiles(self):
    #     '''添加一组新的瓦片'''

    #     filenames, filetype = QFileDialog.getOpenFileNames(None, "添加瓦片", filter="PNG文件(*.png)")
    #     if len(filenames) > 0:
    #         count = Editor.tilelut.load(filenames)
    #         for brush in Editor.tilelut.takeBrushFromBuffer(Editor.brushMaker):
    #             self.tileLib.appendBrush(brush)
    #         warning("添加新的瓦片", f"有{count}块瓦片加载失败")

    def needTile(self, tileId):
        '''检查所有的笔刷是否需要该ID'''

        for brushContainer in self.brushContainerDatas.values():
            if brushContainer.name == self.tileLibName:
                continue
            for brush in brushContainer.brushList:
                if isinstance(brush, Brush):
                    if brush.need(tileId):
                        return True
                elif isinstance(brush, BrushTile):
                    if brush.tileId == tileId:
                        return True
                elif isinstance(brush, BrushUnit):
                    if brush.tileId == tileId:
                        return True
        return False
        
    def nextGroupName(self):
        '''获取一个新的Group名称'''

        count = len(self.brushContainerNames)
        while 1:
            name = f"新建组{count}"
            if name in self.brushContainerNames:
                count += 1
                continue
            return name

    def addGroup(self):
        '''新建一个笔刷组'''

        name = self.nextGroupName()
        self.brushContainerNames.append(name)
        self.brushContainerDatas.setdefault(name, BrushContainer(name))
        self.containerList.add(name)

    def onMoveBrush(self, toGroup:str, brush:Brush):
        '''将Brush从一个组移动到另外的组
        移动分为几种情况:
        0.无法将任何笔刷移动到瓦片库
        1.将瓦片库中的笔刷移动到其他的文件夹中, 该行为不会移动反而会复制一份笔刷到其他的文件夹
        2.其他情况则正常移动和删除'''

        container = Editor.brushList.currentContainer
        if container.name != toGroup:
            # 如果要移动的位置和当前位置一致则忽略这次移动

            if toGroup == self.tileLibName:
                warning("移动笔刷","瓦片库无法放置其他笔刷")
            else:
                _container = self.brushContainerDatas[toGroup]
                if container.name == self.tileLibName:
                    # 情况1, 从瓦片库复制一份笔刷到其他文件夹
                    
                    if not _container.hasBrush(brush):
                        # 目标文件夹中已经有了该笔刷了, 取消复制
                        _container.brushList.append(brush)
                else:
                    # 情况2, 正常复制和移动

                    # 移除笔刷并刷新当前的渲染器
                    container.brushList.remove(brush)           
                    self.renderer.render(container.brushList)
                    _container.brushList.append(brush)

    def getCurrentList(self):
        '''取得当前可用的组合笔刷组'''

        if self.currentContainer is None or self.currentContainer is self.tileLib:
            return None
        return self.currentContainer
    
    def setup(self):
        self.button = EuclidButton(size=(110, 20), title="添加笔刷组", callback=self.addGroup)
        self.button.setParent(self)

        # self.addTileBtn = EuclidButton(size=(110, 20), title="添加瓦片", callback=self.openTiles)
        # self.addTileBtn.move(0, 25)
        # self.addTileBtn.setParent(self)

        self.containerList = SimpleListWidgetSingleBtn(self.onRenamed, self.onDeleted, self.onChoosed, self.onMoveBrush, parent=self)
        self.containerList.setObjectName("EditorBrushContainerList")
        self.containerList.move(0, 25)

    def onRenamed(self, Id, newId) -> bool:
        '''当组重新命名时调用该函数'''
        if Id == self.tileLibName:
            warning("重命名笔刷组", "基础瓦片库不可被重命名")
            return False
        elif newId in self.brushContainerNames:
            warning("重命名笔刷组", "该名称已经被占用")
            return False
        else:
            idx = self.brushContainerNames.index(Id)
            self.brushContainerNames[idx] = newId
            container = self.brushContainerDatas.pop(Id)
            container.name = newId
            self.brushContainerDatas.setdefault(newId, container)
            return True

    def onDeleted(self, Id) -> bool:
        '''当删除该组时调用该函数'''

        if Id == self.tileLibName:
            warning("删除组", "瓦片库不可删除")
        else:
            if questionDelete("是否删除该组") == QMessageBox.Ok:
                self.containerList.takeItem(self.brushContainerNames.index(Id))
                self.brushContainerNames.remove(Id)
                self.brushContainerDatas.pop(Id)
                if self.currentContainer != None and self.currentContainer.name == Id:
                    self.currentContainer = None

    def onChoosed(self, Id) -> bool:
        '''当选择该组时调用该函数'''

        container = self.brushContainerDatas[Id]
        if self.currentContainer != container:
            self.currentContainer = container
            self.renderer.render(container.brushList)

    def resizeEvent(self, evt):
        super().resizeEvent(evt)
        self.containerList.resize(110, self.height() - 25)

class EditorBrushIndicator(QLabel):
    '''单个笔刷渲染器, 展示一张笔刷的图片'''

    def __init__(self, callback, size=(50, 64), parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(QSS_INDICATOR)

        self.pictureBox = QLabel(self)
        self.pictureBox.setAlignment(Qt.AlignCenter)
        self.pictureBox.setFixedSize(size[0], size[0])
        self.pictureBox.move(0, 0)
        self.pictureBox.setObjectName("IndicatorNormal")

        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFixedSize(size[0], size[1] - size[0])
        self.title.move(0, size[0])
        self.title.setObjectName("IndicatorTitle")
        self.callback = callback
        self.brush = None
        self.pressed = False

    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.RightButton:
            self.entryPoint = ev.pos()
            self.pressed = True

    def mouseMoveEvent(self, evt: QMouseEvent) -> None:
        if self.pressed:
            if (evt.pos() - self.entryPoint).manhattanLength() >= QApplication.startDragDistance():
                e = QDrag(self)
                mimeData = QMimeData()
                mimeData.setParent(self)
                mimeData.setProperty("brush", self.brush)
                e.setMimeData(mimeData)
                e.exec_()
        return super().mouseMoveEvent(evt)

    def mouseReleaseEvent(self, evt) -> None:
        if evt.button() == Qt.RightButton:
            self.pressed = False
        elif evt.button() == Qt.LeftButton:
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

    def __init__(self):
        super().__init__(lambda x:QSize(x.width() - 200, x.height() - 30), size=(100, 100))
        self.setStyleSheet("border:1px solid #3f3f3f;border-radius:2px;")
        self.currentSize = (50, 64)
        self.rowCount = 0
        self.recycleQueue = queue.Queue()
        self.indicators = list()
        self.brushList = list()

        self.container = QWidget()
        self.container.setStyleSheet("border:none;")
        self._layout = QGridLayout(self.container)
        self._layout.setAlignment(Qt.AlignLeft| Qt.AlignTop)
        self.setWidget(self.container)

        self.currentBrushIndicator = None
        self.currentBrushList = None                # 与currentBrushIndicator保持同一个阵线

    def reload(self):
        '''重新加载当前的笔刷列表'''
        self.render(self.brushList)

    def onBrushChoozed(self, indicator: EditorBrushIndicator):
        '''选中当前的笔刷 '''

        # 本体状态, 调整当前笔刷与子渲染器状态
        if self.currentBrushIndicator != None:
            if self.currentBrushIndicator != indicator:
                restyle(self.currentBrushIndicator.pictureBox, "IndicatorNormal")
        self.currentBrushIndicator = indicator
        self.currentBrushList = self.brushList
        Editor.onBrushChanged(indicator.brush)
        
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
        self.add(self.pictureBox)

        self.title = EuclidElasticLabel(lambda x:QSize(x.width() - 10, 14), size=(10, 14), text="", center=True)
        self.add(self.title)
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

    def clearBrush(self):
        '''移除当前笔刷'''

        self.title.setText(str())
        self.pictureBox.clear()
        self.brush = None

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if self.brush != None:
            self.showBrush(self.brush)






# --------------- 调色盘窗体 -----------------
# 一个既可以绘制, 也可以用来生产笔刷的窗体

class EditorView(EuclidView):

    def __init__(self, enter, leave, click, move, release, parent=None):
        super().__init__(parent=parent)
        self.click = click
        self.onMove = move
        self.release = release
        self.enter = enter
        self.leave = leave

    def setSelectable(self, value):
        self.setBaseRubberBand(QGraphicsView.RubberBandDrag if value else QGraphicsView.NoDrag)

    def mousePressEvent(self, event):
        self.click(event, super().mousePressEvent(event))
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.release(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.onMove(event)

    def enterEvent(self, event):
        self.enter(event)

    def leaveEvent(self, event):
        self.leave(event)

class EditorToolType:

    NONE = -1
    PEN = 0
    MARQUEE = 1
    ERASE = 2
    FLOODFILL = 3

    # 不允许在此类工具使用期间切换工具
    ROOMCREATOR = 4
    COPY = 5
    POSITION_FINDER = 6

    @staticmethod
    def isConvertable(toolType):
        '''检查当前工具是否可以切换'''
        return toolType < 4

    @staticmethod
    def isNotConvertable(toolType):
        return toolType >= 4


class ITool:
    '''Tool接口, 用于定义Tool的基本行为'''

    def __init__(self, name:str, toolType):
        self.name = name
        self.toolType = toolType
        self.canDraw = False

    def onItemPressed(self, item, event):
        pass

    def onItemMove(self, item, event):
        pass

    def onItemReleased(self, item, event):
        pass

    def onSelectionChanged(self):
        pass

    def onClick(self, event):
        pass

    def onMove(self, event):
        pass

    def onRelease(self, event):
        pass

    def onEnter(self, event):
        pass

    def onLeave(self, event):
        pass

    def done(self):
        pass

    def work(self):
        pass

class BrushTool(ITool):
    '''笔刷工具, 用于在目标tilemap上绘制内容'''

    def __init__(self, renderer: QGraphicsScene, view, tilemap: Tilemap):
        super().__init__("笔刷", EditorToolType.PEN)
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.view = view

        self.isWork = False                             # 笔刷工具是否被启用
        self.currentBrush = None                        # 当前的笔刷
        self.hasBrush = False                           # 当前是否被设置了笔刷
        self.tilemap = tilemap                          # 当前要绘制的数据
        self.drawAs = None                              # 当前的绘制函数
        self.canDraw = False

    def setIndicatorPos(self, pos):
        if self.hasBrush:
            self.currentBrush.indicator.setPos(pos - self.currentBrush.indicatorOffset)

    def work(self):
        self.isWork = True
        if self.hasBrush:
            # 当前已经存在笔刷了
            self.renderer.addItem(self.currentBrush.indicator)
            self.currentBrush.indicator.show()

    def done(self):
        self.isWork = False
        if self.hasBrush:
            self.renderer.removeItem(self.currentBrush.indicator)

    def setBrush(self, brush: BrushTile):
        '''重设笔刷'''

        if self.isWork:
            if self.hasBrush:
                # 已经有了笔刷, 需要移除之前的笔刷的指示器
                self.renderer.removeItem(self.currentBrush.indicator)
            self.renderer.addItem(brush.indicator)
            brush.indicator.show()
        self.hasBrush = True
        self.currentBrush = brush
        self.drawAs = self.drawAsCombination if isinstance(self.currentBrush, Brush) else self.drawAsTile

    def clearBrush(self):
        '''移除当前笔刷工具的笔刷'''

        if self.hasBrush:
            if self.isWork:
                self.renderer.removeItem(self.currentBrush.indicator)
            self.currentBrush = None
            self.hasBrush = False

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

    def onEnter(self, event):
        '''当鼠标进入绘制场景'''

        if self.hasBrush:
            self.currentBrush.indicator.show()
            self.currentBrush.indicator.setPos(self.rendererView.mapToScene(event.pos()))

    def onLeave(self, event):
        if self.hasBrush:
            self.currentBrush.indicator.hide()

    def onClick(self, event):
        if self.hasBrush:
            self.canDraw = True
            pos = self.rendererView.mapToScene(event.pos())
            cpos = EditorUtils.cposUnit(pos)
            indicatorPosition = QPointF(cpos.x() * UNITSIZE, cpos.y() * UNITSIZE) - self.currentBrush.indicatorOffset
            self.currentBrush.indicator.setPos(indicatorPosition)
            if self.currentBrush.draw(cpos, self.tilemap):
                self.drawAs(cpos, indicatorPosition)

    def onRelease(self, event):
        if self.hasBrush:
            self.canDraw = False
            
    def onMove(self, event):
        '''当鼠标移动时'''

        # 调整笔刷指示器的位置
        if self.hasBrush:
            pos = self.rendererView.mapToScene(event.pos())
            cpos = EditorUtils.cposUnit(pos)
            indicatorPosition = QPointF(cpos.x() * UNITSIZE, cpos.y() * UNITSIZE) - self.currentBrush.indicatorOffset
            self.currentBrush.indicator.setPos(indicatorPosition)
            if self.canDraw:
                if self.currentBrush.draw(cpos, self.tilemap):
                    self.drawAs(cpos, indicatorPosition)

class RoomBrushTool(BrushTool):
    '''针对房间的笔刷数据信息'''

    def __init__(self, renderer, view):
        super().__init__(renderer, view, None)
        
        self.roomEntryPosition = QPoint()       # 当前房间的入口点
        self.tilemap = None                     # 当前图层的数据信息
        self.layer = None                       # 当前图层

    def setIndicatorPos(self, pos):
        if self.hasBrush:
            self.currentBrush.indicatorRoom.setPos(pos - self.currentBrush.indicatorOffset)

    def work(self):
        self.isWork = True
        if self.hasBrush:
            # 当前已经存在笔刷了
            self.renderer.addItem(self.currentBrush.indicatorRoom)
            self.currentBrush.indicatorRoom.show()

    def done(self):
        self.isWork = False
        if self.hasBrush:
            self.renderer.removeItem(self.currentBrush.indicatorRoom)
            # self.currentBrush.indicatorRoom.hide()

    def drawAsCombination(self, cpos, indicatorPosiiton):
        '''笔刷是一个组合笔刷'''

        items = self.currentBrush.createRoomTile(self.view, cpos, self.roomEntryPosition)
        for item in items:
            self.renderer.addItem(item)
            self.layer.addTile(item)
        return items

    def drawAsTile(self, cpos, indicatorPosition):
        '''笔刷是一个单瓦片笔刷'''

        item = self.currentBrush.createRoomTile(self.view, cpos)
        self.renderer.addItem(item)
        item.setPos(indicatorPosition)
        self.layer.addTile(item)
        return item

    def onEnter(self, event):
        '''当鼠标进入绘制场景'''

        if self.hasBrush:
            self.currentBrush.indicatorRoom.show()

    def onLeave(self, event):
        if self.hasBrush:
            self.currentBrush.indicatorRoom.hide()

    def setRoom(self, room):
        '''重设当前的房间'''

        self.roomName = room.name
        self.layer = room.currentLayerEntity
        self.tilemap = self.layer.tilemap
        self.roomEntryPosition = QPoint(*room.cpos)

    def setLayer(self, layerEntity):
        '''重设当前的Layer'''

        self.layer = layerEntity
        self.tilemap = layerEntity.tilemap

    def setBrush(self, brush: BrushTile):
        '''重设笔刷'''

        if self.isWork:
            if self.hasBrush:
                # 已经有了笔刷, 需要移除之前的笔刷的指示器
                self.renderer.removeItem(self.currentBrush.indicatorRoom)
            self.renderer.addItem(brush.indicatorRoom)
            brush.indicatorRoom.show()
        self.hasBrush = True
        self.currentBrush = brush
        self.drawAs = self.drawAsCombination if isinstance(self.currentBrush, Brush) else self.drawAsTile

    def clearBrush(self):
        '''移除当前笔刷工具的笔刷'''

        if self.hasBrush:
            if self.isWork:
                self.renderer.removeItem(self.currentBrush.indicatorRoom)
            self.currentBrush = None
            self.hasBrush = False

    def onClick(self, event):
        if self.hasBrush:
            self.canDraw = True
            pos = self.rendererView.mapToScene(event.pos())
            cposRaw = EditorUtils.cposUnit(pos)
            indicatorPosition = EditorUtils.sposUnit(cposRaw) - self.currentBrush.indicatorOffset
            self.currentBrush.indicatorRoom.setPos(indicatorPosition)
            cpos = cposRaw - self.roomEntryPosition
            if self.layer.visible:
                if self.currentBrush.draw(cpos, self.tilemap):
                    self.drawAs(cpos, indicatorPosition)

    def onMove(self, event: QGraphicsSceneMouseEvent):
        if self.hasBrush:
            pos = self.rendererView.mapToScene(event.pos())
            cposRaw = EditorUtils.cposUnit(pos)
            indicatorPosition = EditorUtils.sposUnit(cposRaw) - self.currentBrush.indicatorOffset
            self.currentBrush.indicatorRoom.setPos(indicatorPosition)
            if self.canDraw and self.layer.visible:
                cpos = cposRaw - self.roomEntryPosition
                if self.currentBrush.draw(cpos, self.tilemap):
                    self.drawAs(cpos, indicatorPosition)

    def onRelease(self, event):
        '''当数据发送改变时, 保存当前图层的快照信息'''

        if self.canDraw:
            self.canDraw = False
            self.layer.saveSnapshotWhenChanged()

class MarqueeTool(ITool):

    def __init__(self, renderer: QGraphicsScene, tilemap: Tilemap):
        super().__init__("选框", EditorToolType.MARQUEE)
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.tilemap = tilemap

        # 内部数据
        self.canDraw = False
        self.rawBrush = RawBrush()                                      # 用于生产组合笔刷
        self.rawBrushBorder = QGraphicsRectItem()                       # 组合笔刷边框
        self.rawBrushBorderFlag = False                                 # 记录Border是否存在于场景中, 也可以表示当前是否存在选中的Items
        self.rawBrushBorder.setPen(QPen(QColor("#ff6b97"), 0.7))
        
        self.locationBorder = QGraphicsRectItem()
        self.locationBorderPos = QPointF()
        self.hasLocationBorder = False
        self.locationBorder.setPen(QPen(QColor("#66ffe3"), 0.7))

    def done(self):
        '''如果当前存在选框的话, 则移除选框'''

        if self.rawBrushBorderFlag:
            self.rawBrushBorderFlag = False
            self.renderer.removeItem(self.rawBrushBorder)

    def onItemPressed(self, item, event: QGraphicsSceneMouseEvent):
        self.startPos = event.scenePos()
        self.borderPos = self.rawBrushBorder.pos()
        self.canDraw = True

    def onItemMove(self, item, event: QGraphicsSceneMouseEvent):
        if self.canDraw:
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

        self.canDraw = False
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
            if isinstance(item, TileItem):
                item.back()
        self.rawBrushBorder.setPos(self.borderPos)
        self.locationBorder.setPos(self.borderPos)

    def onSelectionChanged(self):
        '''当选择元素切换时'''

        items = self.renderer.selectedItems()
        if len(items) > 0:
            if len(items) > 1:
                self.rawBrush.loadTiles(items)
            else:
                self.rawBrush.loadTile(items[0])
            self.borderPos = QPointF(self.rawBrush.LB[0] * UNITSIZE, self.rawBrush.LB[1] * UNITSIZE)
            self.rawBrushBorder.setPos(self.borderPos)
            self.locationBorder.setPos(self.borderPos)
            self.rawBrushBorder.setRect(self.rawBrush.rect)
            if not self.rawBrushBorderFlag:
                self.renderer.addItem(self.rawBrushBorder)
                self.rawBrushBorderFlag = True 
        else:
            if self.rawBrushBorder.scene() != None:
                self.renderer.removeItem(self.rawBrushBorder)
            self.rawBrushBorderFlag = False

    def eraseChoosed(self):
        '''清除当前选中的所有单位'''

        if self.rawBrushBorderFlag:
            # 存在border
            for item in self.renderer.selectedItems():
                if isinstance(item, TileItem):
                    self.tilemap.erase(item)
                    self.renderer.removeItem(item)

class RoomMarqueeTool(MarqueeTool):

    def __init__(self, renderer:QGraphicsScene):
        super().__init__(renderer, None)
        self.layer = None
        self.entryPoint = QPoint()
        self.sEntryPoint = QPointF()

    def setRoom(self, room):
        '''设置当前房间 '''

        self.layer = room.currentLayerEntity
        self.tilemap = self.layer.tilemap
        self.entryPoint = QPoint(room.cpos[0], room.cpos[1])
        self.sEntryPoint = self.entryPoint * UNITSIZE
    
    def setLayer(self, layer):
        self.layer = layer
        self.tilemap = layer.tilemap

    def onItemReleased(self, item, event: QGraphicsSceneMouseEvent):
        '''移动结束的时候, 如果移动的长度超过了一个最小网格的阈值, 那么重新调整晶格化位置并重设每个移动过的
        TileItem的网格位置参数, 计算方式通过先计算鼠标想要落位的网格位置, 然后以此网格位置为主来计算晶格化偏移
        最后将此偏移应用到所有的对象'''

        self.canDraw = False
        mousePosition = event.scenePos()
        mouseOffset = mousePosition - self.startPos
        if abs(mouseOffset.x()) > 1 or abs(mouseOffset.y()) > 1:
            coffset = EditorUtils.cposUnit_(mouseOffset)

            if coffset != (0, 0):
                # 要移动的点位确定之后, 之后就是解决能不能移动的问题
                if self.tilemap.canMove(self.rawBrush, coffset):
                    # 可以移动, 则开始移动所有的单位

                    for item in self.renderer.selectedItems():
                        item.applyRoomLatticeOffset(coffset, self.sEntryPoint)
                    self.borderPos += QPointF(coffset[0] * UNITSIZE, coffset[1] * UNITSIZE)
                    self.rawBrushBorder.setPos(self.borderPos)
                    self.clearLocationBorder()
                    self.layer.saveSnapshot()
                    return
        self.resumeRawBrush()
        self.clearLocationBorder()

    def onSelectionChanged(self):
        '''当选择元素切换时'''

        items = self.renderer.selectedItems()
        if len(items) > 0:
            if len(items) > 1:
                self.rawBrush.loadTiles(items)
            else:
                self.rawBrush.loadTile(items[0])
            self.borderPos = self.sEntryPoint + QPointF(self.rawBrush.LB[0] * UNITSIZE, self.rawBrush.LB[1] * UNITSIZE)
            self.rawBrushBorder.setPos(self.borderPos)
            self.locationBorder.setPos(self.borderPos)
            self.rawBrushBorder.setRect(self.rawBrush.rect)
            if not self.rawBrushBorderFlag:
                self.renderer.addItem(self.rawBrushBorder)
                self.rawBrushBorderFlag = True 
        else:
            if self.rawBrushBorder.scene() != None:
                self.renderer.removeItem(self.rawBrushBorder)
            self.rawBrushBorderFlag = False

    def eraseChoosed(self):
        '''清除当前选中的所有单位'''

        if self.rawBrushBorderFlag:
            # 存在border
            for item in self.renderer.selectedItems():
                if isinstance(item, RoomTileItem):
                    self.tilemap.erase(item)
                    self.renderer.removeItem(item)
                    self.layer.tiles.remove(item)

class EraseTool(ITool):

    def __init__(self, renderer: QGraphicsScene, tilemap: Tilemap):
        super().__init__("橡皮", EditorToolType.ERASE)
        self.renderer = renderer
        self.rendererView = self.renderer.views()[0]
        self.tilemap = tilemap

        self.indicator = QGraphicsRectItem(0, 0, UNITSIZE, UNITSIZE)
        self.indicator.setPen(QPen(QColor("#ffffeb"), 0.5))
        self.indicator.setFlag(QGraphicsItem.ItemIsPanel)

        self.transform = QTransform()
        self.offset = QPointF(UNITSIZE/2, UNITSIZE/2)
        self._enabled = False
        self.canDraw = False

    def setIndicatorPos(self, pos):
        self.indicator.setPos(pos)

    def work(self):
        self._enabled = True
        self.renderer.addItem(self.indicator)
        self.indicator.show()

    def done(self):
        self._enabled = False
        self.renderer.removeItem(self.indicator)

    def onEnter(self, event):
        if self._enabled:
            self.indicator.show()

    def onLeave(self, event):
        if self._enabled:
            self.indicator.hide()

    def eraseItems(self):
        '''擦除Items'''

        for item in self.renderer.collidingItems(self.indicator, Qt.IntersectsItemBoundingRect):
            if isinstance(item, TileItem):
                self.tilemap.erase(item)
                self.renderer.removeItem(item)

    def onClick(self, event):

        if self._enabled:
            self.canDraw = True
            self.eraseItems()

    def onRelease(self, event):
        if self.canDraw:
            self.canDraw = False

    def onMove(self, event):
        
        if self._enabled:
            self.indicator.setPos(self.rendererView.mapToScene(event.pos()) - self.offset)
            if self.canDraw:
                self.eraseItems()

class RoomEraseTool(EraseTool):
    '''针对房间的橡皮工具'''

    def __init__(self, renderer: QGraphicsScene):
        super().__init__(renderer, None)
        self.layer = None

    def setRoom(self, room):
        '''重设当前的房间 '''
        self.layer = room.currentLayerEntity
        self.tilemap = self.layer.tilemap

    def setLayer(self, layer):
        '''重设当前的图层'''
        self.layer = layer
        self.tilemap = layer.tilemap

    def eraseItems(self):
        for item in self.renderer.collidingItems(self.indicator, Qt.IntersectsItemBoundingRect):
            if isinstance(item, RoomTileItem):
                if item.checkRoomLayer(self.layer.roomName, self.layer.name):
                    self.tilemap.erase(item)
                    self.renderer.removeItem(item)
                    self.layer.removeTile(item)

    def onClick(self, event):

        if self._enabled:
            self.canDraw = True
            if self.layer.visible:
                self.eraseItems()

    def onMove(self, event):
        
        if self._enabled:
            self.indicator.setPos(self.rendererView.mapToScene(event.pos()) - self.offset)
            if self.canDraw and self.layer.visible:
                self.eraseItems()

    def onRelease(self, event):
        if self.canDraw:
            self.canDraw = False
            self.layer.saveSnapshotWhenChanged()

class RoomTool(ITool):
    '''提供一个用于框选房间范围的工具'''

    def __init__(self, callbackOnReleased, renderer: QGraphicsScene):
        super().__init__("房间创建", EditorToolType.ROOMCREATOR)
        self.callbackOnReleased = callbackOnReleased
        self.renderer = renderer
        self.rendererView = renderer.views()[0]

        self.indicator = QGraphicsRectItem(0, 0, UNITSIZE, UNITSIZE)
        self.indicator.setPen(QPen(QColor("#fcf660")))
        self.roomBorder = QGraphicsRectItem(0, 0, UNITSIZE, UNITSIZE)
        self.roomBorder.setPen(QPen(QColor("#cfff70")))
        self.roomBorder.setBrush(QBrush(QColor(75, 91, 171, 100)))
        self.roomBorderAnnot = Editor.createTextItem("1x1")
        self.roomBorderAnnot.setDefaultTextColor(QColor("#ffffeb"))

        self.enabled = False
        self.indicatorFlag = False
        self.isDrawing = False
        self.hasUpdated = False

    def setIndicatorPos(self, pos):
        self.indicator.setPos(pos)

    def showItem(self):
        if not self.indicatorFlag:
            self.indicatorFlag = True
            self.renderer.addItem(self.indicator)
            
    def hideItem(self):
        if self.indicatorFlag:
            self.indicatorFlag = False
            self.renderer.removeItem(self.indicator)

    def updateMousePosition(self, event):
        self.scenePos = self.rendererView.mapToScene(event.pos())
        self.cpos = EditorUtils.cposUnit(self.scenePos)
        
    def updateRoomBorder(self):
        spos = self.cpos * UNITSIZE
        rect = QRectF(self.entryPosition * UNITSIZE, spos)

        self.roomBorderAnnot.setPlainText(f"{int(abs(rect.width())//UNITSIZE)}x{int(abs(rect.height())//UNITSIZE)}")
        self.roomBorderAnnot.setPos(rect.center() - QPointF(20, 16))
        self.roomBorder.setRect(rect)
        
    def work(self):
        self.enabled = True
        self.entryPosition = QPoint()
        self.cpos = QPoint(UNITSIZE, UNITSIZE)
        self.renderer.addItem(self.roomBorder)
        self.renderer.addItem(self.roomBorderAnnot)
        self.updateRoomBorder()
        self.showItem()

    def done(self):
        self.enabled = False
        self.renderer.removeItem(self.roomBorder)
        self.renderer.removeItem(self.roomBorderAnnot)
        self.hideItem()

    def onEnter(self, event):
        if self.enabled:
            self.showItem()

    def onLeave(self, event):
        if self.enabled:
            self.hideItem()

    def onClick(self, event):
        scenePos = self.rendererView.mapToScene(event.pos())
        self.entryPosition = EditorUtils.cposUnit(scenePos)
        self.isDrawing = True
        self.hasUpdated = False

    def onMove(self, event):
        self.updateMousePosition(event)
        self.indicator.setPos(self.cpos.x() * UNITSIZE, self.cpos.y() * UNITSIZE)
        if self.isDrawing:
            self.hasUpdated = True
            self.updateRoomBorder()

    def onRelease(self, event):
        if self.isDrawing:
            self.isDrawing = False
            if self.hasUpdated:
                self.callbackOnReleased(self.entryPosition, self.cpos)

class RoomFloodFillTool(ITool):
    '''油漆桶工具'''

    def __init__(self, renderer: QGraphicsScene, view):
        super().__init__("油漆桶", EditorToolType.FLOODFILL)
        # 外部数据
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.view = view
        self.tilemap = None
        self.currentBrush = None
        self.entryPoint = QPoint()
        self.layer = None

        # 内部数据
        self.hasBrush = False
        self.isWork = False
        self.drawAs = self.drawAsTile

    def setIndicatorPos(self, pos):
        if self.currentBrush != None:
            self.currentBrush.indicator.setPos(pos - self.currentBrush.indicatorOffset)

    def deleteBrushCheck(self, brush):
        '''删除一个笔刷的时候, 如果该笔刷正在使用的话, 要避免继续使用'''

        if self.currentBrush is brush:
            self.currentBrush is None
            self.hasBrush = False
            if self.isWork:
                self.renderer.removeItem(brush.indicator)

    def drawAsCombination(self, cpos):
        '''笔刷是一个组合笔刷'''

        items = self.currentBrush.createRoomTile(self.view, cpos, self.entryPoint)
        for item in items:
            self.renderer.addItem(item)
            self.layer.addTile(item)
        return items

    def drawAsTile(self, cpos):
        '''笔刷是一个瓦片笔刷'''

        item = self.currentBrush.createRoomTile(self.view, cpos)
        self.renderer.addItem(item)
        item.setPos((cpos + self.entryPoint) * UNITSIZE - self.currentBrush.indicatorOffset)
        self.layer.addTile(item)
        return item

    def setRoom(self, room):
        '''重设当前的房间'''

        self.layer = room.currentLayerEntity
        self.tilemap = self.layer.tilemap
        self.entryPoint = QPoint(*room.cpos)

    def setLayer(self, layer):
        '''重设当前的图层'''

        self.tilemap = layer.tilemap

    def work(self):
        self.isWork = True
        if self.hasBrush:
            self.renderer.addItem(self.currentBrush.indicator)
        
    def done(self):
        self.isWork = False
        if self.hasBrush:
            self.renderer.removeItem(self.currentBrush.indicator)

    def setBrush(self, brush: BrushTile):
        if self.isWork:
            if self.hasBrush:
                self.renderer.removeItem(self.currentBrush.indicatorRoom)
            self.renderer.addItem(self.currentBrush.indicatorRoom)
            self.currentBrush.indicatorRoom.show()
        self.hasBrush = True
        self.currentBrush = brush
        self.drawAs = self.drawAsCombination if isinstance(brush, Brush) else self.drawAsTile

    def clearBrush(self):
        '''移除当前笔刷工具的笔刷'''

        if self.hasBrush:
            if self.isWork:
                self.renderer.removeItem(self.currentBrush.indicatorRoom)
            self.currentBrush = None
            self.hasBrush = False

    def onEnter(self, event):
        if self.hasBrush:
            self.currentBrush.indicator.show()

    def onLeave(self, event):
        if self.hasBrush:
            self.currentBrush.indicator.hide()

    def onClick(self, event):
        '''洪水填充算法'''

        if self.hasBrush:
            spos = self.rendererView.mapToScene(event.pos())
            cpos = EditorUtils.cposUnit(spos) - self.entryPoint
            for pos in self.tilemap.floodFill(self.currentBrush, cpos):
                self.drawAs(QPoint(*pos))

    def onMove(self, event):
        if self.hasBrush:
            spos = self.rendererView.mapToScene(event.pos())
            lspos = EditorUtils.cposUnit(spos) * UNITSIZE - self.currentBrush.indicatorOffset
            self.currentBrush.indicator.setPos(lspos)

    def onRelease(self, event):
        self.layer.saveSnapshotWhenChanged()

class CopyTool(ITool):
    '''复制工具, 当复制确定时, 即复制当前RawBrush当中地数据
    由玩家来确定放置到何处'''

    def __init__(self, renderer: QGraphicsScene, output:callable, toNormal:callable):
        super().__init__("复制工具", EditorToolType.COPY)
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.copyRawData = None
        self.copyItems = list()
        self.copyBorder = QGraphicsRectItem()
        self.copyBorder.setPen(QColor("#3dff6e"))
        self.currentLayer = None
        self.roomEntryPoint = QPoint()
        self.output = output
        self.toNormal = toNormal
        self.hasCopyData = False

    def setCopyData(self, brush: RawBrush):
        '''复制当前地rawBrush数据'''

        self.copyRawData = brush.clone()
        self.copyBorder.setRect(0, 0, brush.width * UNITSIZE, brush.height * UNITSIZE)
        self.hasCopyData = True
        
    def work(self):
        '''启动复制工具'''

        self.renderer.addItem(self.copyBorder)

    def done(self):
        '''关闭复制工具'''

        self.renderer.removeItem(self.copyBorder)

    def setRoom(self, room):
        '''设置当前选中地房间'''

        self.currentLayer = room.currentLayerEntity
        self.roomEntryPoint = QPoint(*room.cpos)
        print(self.roomEntryPoint)

    def setLayer(self, layer):
        '''设置当前地图层'''

        self.currentLayer = layer

    def onClick(self, event):
        if event.button() == Qt.LeftButton:
            # 确认复制
            cposRaw = EditorUtils.cposUnit(self.rendererView.mapToScene(event.pos()))
            cpos = cposRaw - self.roomEntryPoint
            if self.currentLayer.tilemap.drawRaw(cpos, self.copyRawData.narr):
                # 确认可以复制数据
                roomOffset = self.roomEntryPoint * UNITSIZE
                for tile in self.copyRawData.tiles:
                    _tile = tile.clone()
                    _tile.roomName = self.currentLayer.roomName
                    _tile.layerName = self.currentLayer.name
                    _tile.cpos = (_tile.cpos[0] + cpos.x(), _tile.cpos[1] + cpos.y())
                    _tile.reposOffset(roomOffset)
                    self.renderer.addItem(_tile)
                    self.currentLayer.addTile(_tile)
                self.currentLayer.saveSnapshotWhenChanged()
                self.toNormal()
        elif event.button() == Qt.RightButton:
            # 取消复制
            self.toNormal()
        return super().onClick(event)

    def onMove(self, event):
        spos = self.rendererView.mapToScene(event.pos())
        self.copyBorder.setPos(EditorUtils.latticeUnit(spos))

class PositionFinder(ITool):
    '''移动房间工具'''

    def __init__(self, renderer: QGraphicsScene, toNormal: callable):
        super().__init__("移动房间工具", EditorToolType.POSITION_FINDER)
        self.renderer = renderer
        self.rendererView = renderer.views()[0]
        self.border = QGraphicsRectItem()
        self.border.setPen(QColor("#3dff6e"))

        self.handle = None
        self.toNormal = toNormal

    def setBorder(self, size: QSizeF):
        self.border.setRect(0, 0, size.width(), size.height())

    def setHandle(self, handle):
        '''重设当前的处理函数'''
        self.handle = handle
    
    def work(self):
        '''启动位置工具'''

        self.renderer.addItem(self.border)

    def done(self):
        '''关闭位置工具'''

        self.renderer.removeItem(self.border)

    def onClick(self, event):
        if event.button() == Qt.LeftButton:
            if self.handle != None:
                cpos = EditorUtils.cposUnit(self.rendererView.mapToScene(event.pos()))
                self.handle(cpos)
        elif event.button() == Qt.RightButton:
            self.toNormal()

    def onMove(self, event):
        spos = self.rendererView.mapToScene(event.pos())
        self.border.setPos(EditorUtils.latticeUnit(spos))


# --------------- 瓦片实体 --------------------

class TileItem(QGraphicsPixmapItem):
    '''代表一个瓦片的渲染实体, 会记录瓦片的ID和位置'''

    def __init__(self, view, tileId, cpos: tuple, pixmap: QPixmap, shouldInit=True):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsPanel)
        self.view = view

        # 瓦片数据, 和原始瓦片数据类似
        self.tileId = tileId                                            # 0
        self.cpos = cpos                                                # (0, 0)
        if shouldInit:
            self.init()

    def init(self):
        '''初始化基础的数据'''

        pixmap = self.pixmap()
        self.size = EditorUtils.pixmapCSize_(pixmap)                    # (2, 2)
        self.isUnit = self.size == UNITCSIZE                            # False
        self.offset = QPointF(0, self.size[1] * UNITSIZE - pixmap.height())   # QPointF()
        self.repos()
        self.narr = self._toNumpyData()                                 # np.ndarray

    def clone(self):
        '''复制当前的数据'''

        tile = TileItem(self.view, self.tileId, self.cpos, self.pixmap(), shouldInit=False)
        tile.size = self.size
        tile.isUnit = self.isUnit
        tile.offset = QPointF(self.offset)
        tile.narr = np.copy(self.narr)
        return tile

    def repos(self) -> None:
        '''根据自身的cpos重新调整当前瓦片的位置'''

        self.lastPos = self.getScenePosition()
        self.setPos(self.lastPos)
    
    def reposOffset(self, offset: QPointF) -> None:
        '''叠加一个偏移'''

        self.lastPos = self.getScenePosition() + offset
        self.setPos(self.lastPos)

    def getScenePosition(self):
        return QPointF(*self.cpos) * UNITSIZE + self.offset

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
        self.repos()

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

class TileModel:
    '''用于存储到模板库中的TileItem'''

    def __init__(self, tileId:int, cpos:tuple, pixmap:QPixmap):
        self.pixmap = pixmap
        self.tileId = tileId
        self.cpos = cpos

    def createItem(self):
        '''create a new TileItem represent this'''

        item = QGraphicsPixmapItem(self.pixmap)
        item.setFlag(QGraphicsItem.ItemIsPanel)
        item.setPos(QPointF(*self.cpos) * UNITSIZE)
        return item

    def createRoomItem(self, view, offset: QPointF):
        '''当还原时, 创建一个真实的Item'''

        item = RoomTileItem(view, self.tileId, self.cpos, self.pixmap)
        item.reposOffset(offset)
        return item

class RoomTileItem(TileItem):
    '''为房间对象准备的TileItem, 主要增加房间和层级ID信息'''

    def __init__(self, editor, tileId:int, cpos:tuple, pixmap:QPixmap, shouldInit=True) -> None:
        super().__init__(editor, tileId, cpos, pixmap, shouldInit)
        self.roomName = None
        self.layerName = None

    def clone(self):
        '''复制当前的数据'''

        tile = RoomTileItem(self.view, self.tileId, self.cpos, self.pixmap(), shouldInit=False)
        tile.size = self.size
        tile.isUnit = self.isUnit
        tile.offset = self.offset
        tile.narr = np.copy(self.narr)
        return tile

    def checkRoomLayer(self, roomName, layerName):
        return roomName == self.roomName and layerName == self.layerName

    def applyRoomLatticeOffset(self, offset: tuple, sEntryPoint: QPointF):
        '''应用偏移, 重新计算当前的偏移和位置 '''

        self.cpos = (self.cpos[0] + offset[0], self.cpos[1] + offset[1])
        self.reposOffset(sEntryPoint)


# --------------- 调色盘编辑器 -------------------

class EditorPalette(EuclidWindow):
    ''' 地图编辑器调色盘'''

    def __init__(self, parent=None, paletteCanvasSize=(32, 32)):
        '''初始化功能菜单, 调色盘绘制界面和预览界面'''

        super().__init__(parent=parent, title="调色盘")
        self.renderer = EuclidSceneGrid(ltcolor=QColor("#494949"), hvcolor=QColor("#666666"), cellsize=16, lcellsize=10)
        self.renderer.selectionChanged.connect(self.onSelectionChanged)
        self.renderer_view = EditorView(self.onEnter, self.onLeave, self.onClick, self.onMove, self.onRelease)
        self.renderer_view.setScene(self.renderer)
        
        self.tilemapBorder = QGraphicsRectItem(-2, -2, paletteCanvasSize[0] * UNITSIZE + 4, paletteCanvasSize[1] * UNITSIZE + 4)
        self.tilemapBorder.setPen(QPen(QColor("#54adb0")))
        self.tilemapBorder.setFlag(QGraphicsItem.ItemIsPanel)
        self.setup()

        self.editable = False                               # 当前是否可以编辑调色盘
        self.tilemap = Tilemap(csize=paletteCanvasSize)     # 调色盘唯一要维护的数据层
        self.posBuf = QPointF()

        self.brushTool = BrushTool(self.renderer, self, self.tilemap)
        self.eraseTool = EraseTool(self.renderer, self.tilemap)
        self.marqueeTool = MarqueeTool(self.renderer, self.tilemap)
        self.currentTool = self.marqueeTool

    def needTile(self, tileId):
        '''检查调色盘中的数据是否用到了目标Id'''
        return np.any(self.tilemap.data == tileId)

    def handleTilemapBorder(self, value:bool):
        '''根据给定的值来移除或者增加tilemapBorder'''

        if value:
            # add tilemap border
            if self.tilemapBorder.scene() != self.renderer:
                self.renderer.addItem(self.tilemapBorder)
        else:
            # remove tilemap border
            if self.tilemapBorder.scene() != None:
                self.renderer.removeItem(self.tilemapBorder)

    def onItemPressed(self, item: TileItem, event: QGraphicsSceneMouseEvent):
        self.currentTool.onItemPressed(item, event)

    def onItemReleased(self, item: TileItem, event: QGraphicsSceneMouseEvent):
        self.currentTool.onItemReleased(item, event)

    def onItemMoved(self, item: TileItem, event: QGraphicsSceneMouseEvent):
        self.currentTool.onItemMove(item, event)

    def onSelectionChanged(self):
        self.currentTool.onSelectionChanged()

    def onEnter(self, event):
        self.setFocus(True)
        if self.editable:
            self.currentTool.onEnter(event)

    def onLeave(self, event):
        if self.editable:
            self.currentTool.onLeave(event)

    def onClick(self, event, valid):
        if self.editable and valid:
            self.currentTool.onClick(event)

    def onMove(self, event):
        self.posBuf = EditorUtils.latticeUnit(self.renderer_view.mapToScene(event.pos()))
        if self.editable:
            self.currentTool.onMove(event)

    def onRelease(self, event):
        if self.editable:
            self.currentTool.onRelease(event)

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
                brushList.brushList.append(Editor.brushMaker.brushFromRawBrush(self.marqueeTool.rawBrush))
                Editor.brushContainer.reload()

    def resetItemFlags(self, flags):

        for item in self.renderer.items():
            if isinstance(item, TileItem):
                item.setFlags(flags)

    def convertTool(self, toolType):
        '''转换当前的工具类型'''

        # 为了防止相同工具切换
        if self.currentTool.toolType == toolType or self.currentTool.canDraw:
            return            

        self.currentTool.done()
        self.toolType = toolType
        if toolType == EditorToolType.PEN:

            # 外观
            self.statusLabel.setText("编辑调色盘")
            self.infobar.normal("编辑中..")
            self.statusIndicator.run()

            # 数据
            self.editable = True
            self.renderer_view.setSelectable(False)
            self.currentTool = self.brushTool
            self.brushTool.work()
            self.brushTool.setIndicatorPos(self.posBuf)
            
            # 行为
            self.handleTilemapBorder(True)
            self.resetItemFlags(QGraphicsItem.ItemIsPanel)

        elif toolType == EditorToolType.MARQUEE:
            self.editable = False
            self.renderer_view.setSelectable(True)
            self.statusLabel.setText("笔刷选择")
            self.statusIndicator.normal()
            self.currentTool = self.marqueeTool
            self.infobar.normal("调色盘进入选择模式")
            self.resetItemFlags(QGraphicsItem.ItemIsMovable|QGraphicsItem.ItemIsSelectable)
            self.handleTilemapBorder(True)
            self.tilemapBorder.setZValue(-9999)

        elif toolType == EditorToolType.ERASE:
            self.editable = True
            self.renderer_view.setSelectable(False)
            self.statusLabel.setText("编辑调色盘")
            self.statusIndicator.run()
            self.currentTool = self.eraseTool
            self.eraseTool.work()
            self.eraseTool.setIndicatorPos(self.posBuf)
            self.infobar.normal("编辑中..")
            self.handleTilemapBorder(False)
            self.resetItemFlags(QGraphicsItem.ItemIsPanel)


    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Escape:
            self.convertTool(EditorToolType.MARQUEE)
        elif event.key() == Qt.Key_B:
            self.convertTool(EditorToolType.PEN)
        elif event.key() == Qt.Key_E:
            self.convertTool(EditorToolType.ERASE)
        elif event.key() == Qt.Key_Delete:
            if self.currentTool is self.marqueeTool:
                self.marqueeTool.eraseChoosed()
        
    def debug(self):
        '''显示当前的地图数据'''

        print(self.tilemap.data.transpose(1, 0))

    def debug2(self):
        for item in self.renderer.items():
            if isinstance(item, TileItem):
                print(item)

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


        _func = lambda x: QSize(x.width() - 10, max(x.height() - 50, 100))
        self._container.add(EuclidElasticDocker(_func, self.renderer_view, size=(100, 100)))
        
        self.editBtn = EuclidButton(title="编辑调色盘", callback=lambda:self.convertTool(EditorToolType.PEN), size=(120, 20))
        self._container.add(self.editBtn)

        self.createBrushBtn = EuclidButton(title="创建组合笔刷", callback=self.createCombineBrush)
        self._container.addh(self.createBrushBtn)

        self.debugBtn = EuclidButton(title="测试", callback=self.debug)
        self._container.addh(self.debugBtn)

        self.debugBtn2 = EuclidButton(title="测试2", callback=self.debug2)
        self._container.addh(self.debugBtn2)

class LayerSnapshot:
    '''层级快照, 记录当前层级的数据状态, 以备后续还原'''

    def __init__(self, layer):
        '''和复制不太一样, 快照只是保存所有瓦片的ID和位置, 其他数据一律从瓦片查找表中获取'''

        # 记录所有瓦片的ID和位置，以备后续还原
        self.narr = np.copy(layer.tilemap.data)
        self.tiles = dict()
        for tile in layer.tiles:
            self.tiles.setdefault(tile.cpos, tile.tileId)

    def needTile(self, tileId:int) -> bool:
        return np.any(self.narr == tileId)

    def restore(self, layer, view, offset, renderer):
        layer.tilemap.data = self.narr

        # 清空原来的数据
        for tile in layer.tiles:
            renderer.removeItem(tile)
        layer.tiles.clear()

        # 将快照中的数据重新录入层级
        for cpos, Id in self.tiles.items():
            item = RoomTileItem(view, Id, cpos, Editor.tilelut.fetchPixmap(Id))
            item.reposOffset(offset)
            renderer.addItem(item)
            layer.addTile(item)

# ------------------------- 主编辑器 ---------------------------------

class MapEditorRuntimePreviewWindow(EuclidWindow):
    '''地图编辑器实时预览窗体'''

    def __init__(self, renderer: QGraphicsScene, parent=None):
        super().__init__(parent=parent, title="地图预览")
        self.rendererView = EditorView(self.empty, self.empty, self.onClick, self.empty, self.empty)
        self.rendererView.setScene(renderer)
        self.rendererView.setSelectable(False)
        self.renderer = renderer
        self.hasChangeSelectable = False
        self.setup()

    def empty(self, event):
        pass

    def onClick(self, event, valid):
        pass

    def enterEvent(self, ev) -> None:
        self.hasChangeSelectable = Editor.mapEditor._disableSelections()
        return super().enterEvent(ev)

    def leaveEvent(self, ev) -> None:
        if self.hasChangeSelectable:
            Editor.mapEditor._enableSelections()
        return super().leaveEvent(ev)

    def setup(self):
        self.add(EuclidElasticDocker(EuclidGeometry.fullsizeGap((10, 10)), self.rendererView, size=(100, 100)))

class RoomHandlerWindow(EuclidWindow):
    '''房间处理器, 提供更多的对房间的操作
    1.支持将房间当前的数据作为模板导出
    2.支持将房间模板库中的数据直接倒入选中的房间中'''

    def __init__(self, parent=None):
        super().__init__(parent=parent, title="房间模板库")
        self.renderer = EuclidSceneGrid(ltcolor=QColor("#494949"), hvcolor=QColor("#666666"), cellsize=16, lcellsize=10)
        self.rendererView = EditorView(self.empty, self.empty, self.onClick, self.empty, self.empty)
        self.rendererView.setScene(self.renderer)
        self.rendererView.setSelectable(False)
        self.listView = QListView()
        self.listView.clicked.connect(self.onTemplateChoosed)
        self.listView.setObjectName("EditorBrushContainerList")
        self.stringListModel = QStringListModel([])
        self.listView.setModel(self.stringListModel)
        self.listView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.libNames = ["默认模板库"]
        self.libs = {"默认模板库":[]}
        self.currentLibName = "默认模板库"
        self.currentRoom = None
        self.setup()

    def toJson(self):
        '''转换为json数据'''

        output = list()
        for name in self.libNames:
            lib = self.libs[name]
            libData = [room.toJson() for room in lib]
            output.append({"name":name,"roomList":libData})
        return output

    def fromJson(self, libList):
        '''从json数据中还原信息'''

        self.libNames.clear()
        self.libs.clear()
        for libInfo in libList:
            self.libNames.append(libInfo["name"])
            lib = list()
            for o in libInfo["roomList"]:
                room = Room(o["name"], tuple(o["pos"]), tuple(o["size"]), createRoomBorder=False)
                room.fromJsonAsTemplate(o)
                lib.append(room)
            self.libs.setdefault(libInfo["name"], lib)

        self.comboBox.clear()
        self.comboBox.addItems(self.libNames)
        if len(self.libNames) > 0:
            self.comboBox.setCurrentIndex(0)
            self.onGroupChanged(0)

    def invalid(self):
        '''禁用窗体控件'''

        self.addGroupBtn.invalid()
        self.removeGroupBtn.invalid()
        self.recordBtn.invalid()
        self.generateBtn.invalid()
        self.removeRoomBtn.invalid()

    def resume(self):
        '''恢复当前的窗体'''

        self.addGroupBtn.resume()
        self.removeGroupBtn.resume()
        self.recordBtn.resume()
        self.generateBtn.resume()
        self.removeRoomBtn.resume()

    def fetchCurrentTemplate(self):
        '''获取当前的模板对象'''

        if self.currentLibName is None:
            return None
        roomIdx = self.listView.currentIndex().row()
        if roomIdx < 0:
            return None
        return self.libs[self.currentLibName][self.listView.currentIndex().row()]

    def needTile(self, tileId) -> bool:
        '''检查模板库的中任何一个模板是否用到了目标瓦片'''

        for lib in self.libs.values():
            for template in lib:
                if template.needTile(tileId):
                    return True
        return False

    def onTemplateChoosed(self):
        idx = self.listView.currentIndex().row()
        room = self.libs[self.currentLibName][idx]
        self.currentTemplateInfo.warning(f"{room.name}:房间大小_{room.csize}")

        self.renderer.clear()
        for layer in room.layers.values():
            for tile in layer.tiles:
                self.renderer.addItem(tile.createItem())
        self.renderer.addItem(room.createRoomBorder())

    def onRoomChoosed(self, room):
        '''当选择了一个新的房间'''

        self.currentRoom = room
        if room is None:
            self.indicator.invalid()
            self.statusInfo.normal(("暂无信号"))
            self.contentBar.normal("..")
        else:
            self.indicator.normal()
            self.statusInfo.setText(f"房间名:{room.name}")
            self.contentBar.success((f"房间位置:{room.cpos},房间大小:{room.csize}"))

    def record(self):
        '''将当前房间存储为模板房间'''

        if self.currentRoom is None:
            warning("存储为模板", "当前没有房间信号")
        elif self.currentLibName is None:
            warning("存储为模板", "当前没有选中任何组")
        else:
            if self.currentRoom.isEmptyRoom():
                warning("存储为模板", "空房间不可记录为模板")
            else:
                dialog = ProjectCreator(self._record, None, title="存储为模板", content="输入模板名")
                dialog.exec_()

    def _record(self, name):
        '''将当前房间存储为模板'''

        titles = self.stringListModel.stringList()
        if name in titles:
            warning("存储为模板", "组中已有同名模板")
            return False
        else:
            titles.append(name)
            self.stringListModel.setStringList(titles)
            roomClone = self.currentRoom.clone()
            roomClone.name = name
            self.libs[self.currentLibName].append(roomClone)
            return True

    def _addGroup(self, name):
        '''创建一个新的模板'''

        if name in self.libNames:
            warning("错误报告", "存在相同名称的组")
            return False
        else:
            self.libNames.append(name)
            self.libs.setdefault(name, list())
            self.comboBox.addItem(name)
            return True

    def addGroup(self):
        dialog = ProjectCreator(self._addGroup, None, title="新建模板组",content="输入组名")
        dialog.exec_()
    
    def onGroupChanged(self, index):
        print(f"选中组:{self.libNames[index]}")
        self.currentLibName = self.libNames[index]
        self.loadGroup(self.libs[self.currentLibName])

    def removeGroup(self):
        if questionDelete("是否删除组") == QMessageBox.Ok:
            idx = self.comboBox.currentIndex()
            self.comboBox.removeItem(idx)
            self.libNames.pop(idx)
            
            currentIdx = self.comboBox.currentIndex()
            if currentIdx != -1:
                self.currentLibName = self.libNames[currentIdx]
                self.loadGroup(self.libs[self.currentLibName])
            else:
                self.currentLibName = None
                self.stringListModel.setStringList([])
        
    def loadGroup(self, roomList:list):
        '''在listView中加载一个当前的组'''

        self.stringListModel.setStringList([room.name for room in roomList])
        self.renderer.clear()

    def restoreRoom(self):
        '''将当前重新还原到地图编辑器中'''

        template = self.fetchCurrentTemplate()
        if template is None:
            warning("还原房间", "请选择要还原的房间")
        else:
            Editor.mapEditor.onRestoreRoom(template)

    def removeRoom(self):
        '''删除当前的模板'''

        if self.currentLibName != None:
            templateList = self.libs[self.currentLibName]
            idx = self.listView.currentIndex().row()
            if idx >= 0:
                if questionDelete("是否删除模板") == QMessageBox.Ok:
                    self.renderer.clear()
                    templateList.pop(idx)
                    titles = self.stringListModel.stringList()
                    titles.pop(idx)
                    self.stringListModel.setStringList(titles)
            else:
                warning("删除当前模板", "当前没有选中房间")
        else:
            warning("删除当前模板", "当前没有组")

    def empty(self, ev):
        pass

    def onClick(self, ev, valid):
        pass

    def setup(self):

        self.indicator = EuclidMiniIndicator()
        self.indicator.invalid()
        self.statusInfo = EuclidLabel(text="暂无信号", size=(120, 14))
        self.spilter = EuclidLabel(size=(15, 14), text="|", center=True)
        self.contentBar = EuclidElasticLabel(lambda x:QSize(x.width() - 150, 14), text="..")
        self.recordBtn = EuclidButton(title="存储为模板", callback=self.record)
        self.addGroupBtn = EuclidButton(title="添加组", callback=self.addGroup)
        self.removeGroupBtn = EuclidButton(title="删除组", callback=self.removeGroup)
        self.generateBtn = EuclidButton(title="还原房间", callback=self.restoreRoom)
        self.removeRoomBtn = EuclidButton(title="删除房间", callback=self.removeRoom)
        restyle(self.removeGroupBtn, EuclidNames.BUTTON_RED)
        restyle(self.removeRoomBtn, EuclidNames.BUTTON_RED)

        self.comboBox = EuclidComboBox(lambda x:QSize(x.width() - 10, 15), size=(80, 20))
        self.comboBox.addItems(self.libNames)
        self.comboBox.currentIndexChanged.connect(self.onGroupChanged)
        self.currentTemplateInfo = EuclidElasticLabel(lambda x: QSize(x.width() - 20, 14), size=(50, 14), text="当前没有模板")

        self.add(self.indicator)
        self.addh(self.statusInfo)
        self.addh(self.spilter)
        self.addh(self.contentBar)
        self.add(EuclidLabel(text="模板组", size=(40,20)))
        self.addh(EuclidDocker(self.comboBox, size=(120, 20)))

        self.add(self.addGroupBtn)
        self.addh(self.removeGroupBtn)
        self.add(self.recordBtn)
        self.addh(self.generateBtn)
        self.addh(self.removeRoomBtn)
        self.add(EuclidElasticDocker(lambda x: QSize(80, x.height() - 125), self.listView, size=(50, 50)))

        resizefunc = lambda x: QSize(x.width() - 95, x.height() - 125)
        self.addh(EuclidElasticDocker(resizefunc, self.rendererView, size=(50, 50)))
        self.add(self.currentTemplateInfo)

class MapEditor(EuclidWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent, title="地图编辑器")
        self.renderer = EuclidSceneGrid(ltcolor=QColor("#494949"), hvcolor=QColor("#666666"), cellsize=16, lcellsize=10)
        self.rendererView = EditorView(self.onEnter, self.onLeave, self.onClick, self.onMove, self.onRelease)
        self.rendererView.setScene(self.renderer)
        self.renderer.selectionChanged.connect(self.onSelectionChanged)

        self.setup()
        self.marqueeTool = RoomMarqueeTool(self.renderer)
        self.brushTool = RoomBrushTool(self.renderer, self)
        self.eraseTool = RoomEraseTool(self.renderer)
        self.roomTool = RoomTool(self.onRoomBorderMaked, self.renderer)
        self.floodFillTool = RoomFloodFillTool(self.renderer, self)
        self.copyTool = CopyTool(self.renderer, self.info.normal, lambda:self.convertTool(EditorToolType.MARQUEE))
        self.positionFinder = PositionFinder(self.renderer, self._cancelRestore)
        self.emptyTool = ITool("空白", EditorToolType.NONE)

        self.currentTool = self.emptyTool
        self.projectName = None
        self.posBuf = QPointF()

        # 记录房间信息
        self.rooms = None
        self.currentRoom = None

        # 调整房间大小
        self.isAdjustRoom = False
        self.adjustRoom = None

    def exportMapData(self):
        '''导出现有的地图数据, 导出瓦片查找表和房间数据到同一个json文件中'''

        if self.rooms != None:
            lut = Editor.tilelut.exportAsJson()
            rooms = self.toJson()
            return {"lut":lut, "rooms":rooms}
        else:
            warning("导出数据失败", "当前没有可导出内容(- -.)")
            return None

    def toJson(self):
        '''将所有的房间信息转换为json数据'''
        return [room.toJson() for room in self.rooms.values()]

    def fromJson(self, o:list):
        '''用当前的json数据来覆盖现有的房间列表'''

        self.rooms = dict()
        for info in o:
            room = Room(info["name"], info["pos"], info["size"])
            room.fromJsonInMapEditor(info, self, self.renderer)
            self.rooms.setdefault(info["name"], room)
        self.roomList.setRooms(self.rooms)

    def invalid(self):
        '''禁用当前窗体的控件'''

        self.roomList.invalid()
        self.layerList.invalid()

    def resume(self):
        '''恢复当前窗体的控件'''

        self.layerList.resume()
        self.roomList.resume()

    def saveCurrentData(self):
        '''保存当前的数据 '''

    def checkHasSaved(self):
        '''检查是否有数据发生变动'''

        for room in self.roomList.rooms.values():
            if not room.checkHasSaved():
                return False
        return True

    def questionSave(self, handle):
        '''当要改动当前的工程项目时,优先询问是否保存'''

        if self.projectName is None:
            handle()
        else:
            # 创建工程之前优先检查是否已经保存了当前数据，如果没有保存，优先询问是否保存当前数据
            # 如果用户抛弃当前数据，直接进入创建阶段，否则保存当前数据并跳过创建
            if self.checkHasSaved():
                # 当前已经保存了
                handle()
            else:
                result = QMessageBox.question(None, "创建新的工程", "当前数据还未保存, 是否存储", QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
                if result == QMessageBox.Save:

                    self.saveCurrentData()
                elif result == QMessageBox.Cancel:

                    self.info.normal("取消创建副本")
                elif result == QMessageBox.Discard:

                    handle()

    def _createNewInstance(self):
        '''确认当前数据已经保存后，创建一个新的副本'''
        filepath, filetype = QFileDialog.getOpenFileName(None, "选择瓦片查找表", filter="ZIP文件(*.zip)")
        if len(filepath) > 0:
            if Editor.loadTileLut(filepath):
                def _create(projectName:str):
                    self.projectName = projectName
                    self.hasSaved = True
                    self.rooms = dict()
                    self.roomList.setRooms(self.rooms)
                    self.statusLabel.normal(f"工程:{projectName}")
                    self.statusIndicator.normal()
                    self.info.normal("工程创建完毕..")
                    Editor.resumeAll()
                    return True
                dialog = ProjectCreator(_create, None)
                dialog.exec_()
            else:
                warning("创建副本错误", "目标查找表文件无效")

    def _toEdit(self, text, tool):
        '''将地图编辑器现有的指示器转换为编辑状态'''

        self.statusIndicator.run()
        self.rendererView.setSelectable(False)
        if self.currentRoom != None:
            self.currentRoom.currentLayerEntity.setLayerSelectable(False)
        self.statusLabel.setText(text)
        self.currentTool = tool
        self.currentTool.work()

    def convertTool(self, toolType):
        '''转换当前所使用的工具 '''

        if self.currentTool.toolType == toolType:
            # 房间创造器模式只能通过房间辅助创造器退出
            return False
        if self.currentTool.canDraw:
            return False

        self.currentTool.done()
        if toolType == EditorToolType.PEN:
            self._toEdit("编辑->笔刷", self.brushTool)
            self.brushTool.setIndicatorPos(self.posBuf)

        elif toolType == EditorToolType.ERASE:
            self._toEdit("编辑->橡皮", self.eraseTool)
            self.eraseTool.setIndicatorPos(self.posBuf)

        elif toolType == EditorToolType.MARQUEE:
            self.statusIndicator.normal()
            self.rendererView.setSelectable(True)
            if self.currentRoom != None:
                self.currentRoom.currentLayerEntity.setLayerSelectable(True)
            self.statusLabel.setText("调整->选框")
            self.currentTool = self.marqueeTool
            self.marqueeTool.work()

        elif toolType == EditorToolType.FLOODFILL:
            self._toEdit("编辑->油漆桶", self.floodFillTool)
            self.floodFillTool.setIndicatorPos(self.posBuf)

        elif toolType == EditorToolType.COPY:
            self._toEdit("选框->复制", self.copyTool)

        elif toolType == EditorToolType.POSITION_FINDER:
            self._toEdit("选框->房间处理", self.positionFinder)

    def needTile(self, tileId):
        '''检查目标数据中是否出现了瓦片ID'''

        for room in self.roomList.rooms.values():
            if room.needTile(tileId):
                return True
        return False

    def _disableSelections(self):
        '''由预览窗体调用,当进入预览窗体时, 如果当前工具是选择工具, 则禁用当前选择'''

        if self.currentTool is self.marqueeTool:
            if self.currentRoom != None:
                self.currentRoom.currentLayerEntity.setLayerSelectable(False)
                return True
        return False

    def _enableSelections(self):
        self.currentRoom.currentLayerEntity.setLayerSelectable(True)

    # ------------- 关于房间 -----------------

    def resetRoomForTools(self, room):
        self.marqueeTool.setRoom(room)
        self.brushTool.setRoom(room)
        self.eraseTool.setRoom(room)
        self.floodFillTool.setRoom(room)
        self.copyTool.setRoom(room)

    def onLayerChoosed(self, Id):
        '''回调函数: 当用户选择一个图层时, 执行该函数
        调整当前所有工具的绘制数据'''

        self.currentRoom.setCurrentLayer(Id)
        self.info.normal(f"当前数据: {self.currentRoom.name}-{Id}")
        self.layerList.listView.setCurrentRow(self.currentRoom.layerNames.index(Id))

        # 重设所有工具当前的图层
        layer = self.currentRoom.layers.get(Id)
        self.brushTool.setLayer(layer)
        self.eraseTool.setLayer(layer)
        self.marqueeTool.setLayer(layer)
        self.floodFillTool.setLayer(layer)
        self.copyTool.setLayer(layer)
        if self.currentTool is self.marqueeTool:
            layer.setLayerSelectable(True)

    def onLayerDeleted(self, Id):
        '''回调函数: 当准备删除一个图层时, 执行该函数'''
        
        if len(self.currentRoom.layerNames) > 1:
            if questionDelete("删除图层"):
                self.currentRoom.layerNames.remove(Id)
                layer = self.currentRoom.layers.pop(Id)
                for tile in layer.tiles:
                    self.renderer.removeItem(tile)
                self.layerList.reloadRoom()
                self.onLayerChoosed(self.currentRoom.layerNames[0])
        else:
            warning("删除图层", "至少保留一个图层")

    def createRoomCreatorHelper(self, parent):
        '''创建room辅助创建器'''

        self.roomHelper = RoomCreatorHelper(self.onRoomHelperConfirm, self.onRoomHelperCancel, parent=parent)
        self.roomHelper.hide()
        return self.roomHelper

    def onRoomChoozed(self, room):
        '''当房间被重新选择时, 执行该回调函数'''

        if self.currentRoom != None:
            self.currentRoom.normal()
            self.currentRoom.currentLayerEntity.setLayerSelectable(False)

        self.currentRoom = room
        if room != None:
            self.currentRoom.choosed()
            self.layerList.setRoom(room)
            self.resetRoomForTools(room)
            if self.currentTool is self.marqueeTool:
                self.currentRoom.currentLayerEntity.setLayerSelectable(True)
            
        Editor.roomHandler.onRoomChoosed(room)

    def createNewRoom(self, title):
        '''启动房间创造单位'''

        self.currentTool.done()                 # 停用当前的工具
        if self.currentRoom != None:
            self.currentRoom.currentLayerEntity.setLayerSelectable(False)

        self.currentTool = self.roomTool
        self.currentTool.work()
        self.rendererView.setSelectable(False)
        self.roomHelper.show()
        self.roomHelper.setTitle(title)
        self.roomHelper.move(self.pos() + QPoint(100, 100))
        self.invalid()

    def onRoomBorderMaked(self, cpos1: QPoint, cpos2:QPoint):
        '''回调函数: 创建房间时, 当房间框选完毕时执行改函数
        主要用以确认当前房间是否可以创建'''

        p1 = min(cpos1.x(), cpos2.x()), min(cpos1.y(), cpos2.y())
        size = abs(cpos1.x() - cpos2.x()), abs(cpos1.y() - cpos2.y())
        p2 = p1[0] + size[0], p1[1] + size[1]

        if self.isAdjustRoom:
            if self.roomList.collisionExcept(self.adjustRoom.name, p1, p2):
                self.roomHelper.collisionWarning()
            else:
                lb, rt = self.adjustRoom.constraint()
                asize = rt[0] - lb[0], rt[1] - lb[1]
                print(f"约束的范围是:{lb},{rt}")
                print(f"框选的范围是:{p1},{size}")
                if size[0] < asize[0] or size[1] < asize[1]:
                     self.roomHelper.sizeWarning()
                else:
                     self.roomHelper.receiveAdjustData(p1, size, lb, rt)
        else:
            if self.roomList.collisionAny(p1, p2):
                self.roomHelper.collisionWarning()
            else:
                self.roomHelper.receiveData(p1, size)

    def onRoomHelperConfirm(self):
        '''确认创建房间, 函数会通过Editor绑定给RoomCreateHelper'''

        if self.isAdjustRoom:
            # 调整房间
            self.adjustRoom.adjust(*self.roomHelper.adjustArgs())
            self.onRoomHelperCancel()
            self.resetRoomForTools(self.adjustRoom)
            Editor.roomHandler.onRoomChoosed(self.adjustRoom)
            self._releaseToolBuf()
        else:
            # 创建房间
            room = self.roomList.createRoom(self.roomHelper.cpos, self.roomHelper.csize)
            self.renderer.addItem(room.roomBorder)
            self.onRoomHelperCancel()
            if self.currentRoom is None:
                self.onRoomChoozed(room)
                self.onLayerChoosed(room.currentLayer)

    def onRoomHelperCancel(self):
        '''取消创建房间, 函数会通过Editor绑定给RoomCreateHelper'''
        
        self.currentTool.done()
        self.currentTool = self.emptyTool
        self.resume()
        Editor.roomCreatorHelper.hide()

    def onRoomVisibleChanged(self, Id, v):
        '''当房间的是否可见改变时执行该回调函数'''

        room = self.roomList.rooms[Id]
        for layer in room.layers.values():
            layer.setVisible(v)
        if self.currentRoom.name == Id:
            self.layerList._setVisible(v)

    def onRoomDelete(self, Id):
        '''删除当前的房间'''

        self.roomList.removeRoom(Id, self.renderer)
        if self.currentRoom.name == Id:
            if len(self.roomList.rooms) > 0:
                self.onRoomChoozed(self.roomList.firstRoom())
            else:
                self.layerList.listView.clear()
                self.onRoomChoozed(None)

    def onAdjustRoom(self, Id):
        '''调整当前房间的大小'''

        if self.currentRoom is None:
            warning("调整房间大小", "请选中一个当前的房间")
        else:
            self._recordTool()
            self.isAdjustRoom = True
            self.adjustRoom = self.currentRoom
            self.createNewRoom("调整房间")

    def onCreateRoom(self):
        '''创建新的房间'''

        self.isAdjustRoom = False
        self.createNewRoom("创建房间")

    def onMoveRoom(self):
        '''移动当前房间到新的位置'''

        if self.currentRoom is None:
            self.outputError("当前没有任何房间")
        else:
            self._recordTool()
            self.moveRoom = self.currentRoom
            self.positionFinder.setBorder(self.currentRoom.roomBorder.rect().size())
            self.positionFinder.setHandle(self._onMoveRoomConfirm)
            self.convertTool(EditorToolType.POSITION_FINDER)
            self.invalid()

    def _onMoveRoomConfirm(self, cpos):
        '''确认放置当前房间'''

        _cpos = (cpos.x(), cpos.y())
        _cpos2 = cpos.x() + self.moveRoom.csize[0], cpos.y() + self.moveRoom.csize[1]
        if self.roomList.collisionExcept(self.moveRoom.name, _cpos, _cpos2):
            # 首先确认目标位置是否会和其他房间冲突
            warning("移动房间", "当前位置和其他房间冲突")
        else:
            self.moveRoom.move(_cpos)
            self._releaseToolBuf()
            self.resetRoomForTools(self.moveRoom)
            Editor.roomHandler.onRoomChoosed(self.moveRoom)
            self.resume()

    def onRestoreRoom(self, room):
        '''用模板创建一个新的房间'''

        if EditorToolType.isConvertable(self.currentTool.toolType):
            # 当前工具可以切换
            self._recordTool()
            self.restoredRoom = room
            self.positionFinder.setBorder(room.rectRaw())
            self.positionFinder.setHandle(self._onRestoreRoomConfirm)
            self.convertTool(EditorToolType.POSITION_FINDER)
            self.invalid()
            self.output("右键可退出当前工具")
        else:
            self.outputError("当前状态不可以创建新的房间")

    def _onRestoreRoomConfirm(self, cpos):
        '''当确认房间位置时'''

        p1 = cpos.x(), cpos.y()
        p2 = p1[0] + self.restoredRoom.csize[0], p1[1] + self.restoredRoom.csize[1]
        if self.roomList.collisionAny(p1, p2):
            # 是否和任何房间冲突
            warning("还原房间", "和其他房间冲突")
        else:
            self.roomList.restoreRoom(p1, self.restoredRoom, self, self.renderer)

    def _cancelRestore(self):
        '''停止还原'''

        self.resume()
        self._releaseToolBuf()

    def _recordTool(self):
        self.toolBuf = self.currentTool.toolType
    
    def _releaseToolBuf(self):
        if self.toolBuf != EditorToolType.NONE:
            self.convertTool(self.toolBuf)
        else:
            self.convertTool(EditorToolType.MARQUEE)
    
    # --------------- 关于事件 -----------------
    def keyPressEvent(self, ev) -> None:
        if self.currentRoom is None:
            self.outputError("没有任何房间")
            return

        if EditorToolType.isNotConvertable(self.currentTool.toolType):
            self.outputError("当前不可切换工具")
            return

        if ev.key() == Qt.Key_B:
            self.convertTool(EditorToolType.PEN)
        elif ev.key() == Qt.Key_E:
            self.convertTool(EditorToolType.ERASE)
        elif ev.key() == Qt.Key_Escape or ev.key() == Qt.Key_Space:
            self.convertTool(EditorToolType.MARQUEE)
        elif ev.key() == Qt.Key_Delete:
            if self.currentTool is self.marqueeTool:
                self.marqueeTool.eraseChoosed()
        elif ev.key() == Qt.Key_G:
            self.convertTool(EditorToolType.FLOODFILL)
        elif ev.key() == Qt.Key_C and ev.modifiers() & Qt.ControlModifier:
            if self.currentTool is self.marqueeTool and self.marqueeTool.rawBrushBorderFlag:
                # 复制数据并启动复制工具
                
                self.copyTool.setCopyData(self.marqueeTool.rawBrush)
                self.convertTool(EditorToolType.COPY)
            else:
                if self.copyTool.hasCopyData:
                    self.convertTool(EditorToolType.COPY)
        elif ev.key() == Qt.Key_Q:
            # 移动房间
            if not self.currentTool.canDraw:
                if self.currentTool != self.positionFinder:
                    self.onMoveRoom()
            else:
                self.outputError("当前工具正在使用中")
        elif ev.key() == Qt.Key_Z:
            if EditorToolType.isConvertable(self.currentTool.toolType):
                if self.currentRoom != None:
                    self.currentRoom.currentLayerEntity.restoreSnapshot(self, self.renderer)

    def onItemPressed(self, item, event):
        self.currentTool.onItemPressed(item, event)

    def onItemReleased(self, item, event):
        self.currentTool.onItemReleased(item, event)

    def onItemMoved(self, item, event):
        self.currentTool.onItemMove(item, event)

    def onEnter(self, event):
        self.setFocus(True)
        self.currentTool.onEnter(event)

    def onLeave(self, event):
        self.currentTool.onLeave(event)

    def onClick(self, event, valid):
        if valid:self.currentTool.onClick(event)

    def onMove(self, event):
        self.posBuf = EditorUtils.latticeUnit(self.rendererView.mapToScene(event.pos()))
        self.currentTool.onMove(event)

    def onRelease(self, event):
        self.currentTool.onRelease(event)

    def onSelectionChanged(self):
        self.currentTool.onSelectionChanged()

    def outputError(self, content):
        '''输出错误信息'''
        self.info.error(f"[{now()}] {content}")

    def output(self, content):
        '''输出错误信息'''
        self.info.normal(f"[{now()}] {content}")

    def outputSuccess(self, content):
        '''输出错误信息'''
        self.info.success(f"[{now()}] {content}")

    def debug(self):
        if self.currentRoom != None:
            print("- 层级瓦片数据测试 -")
            print(self.currentRoom.currentLayerEntity.tilemap.data.transpose(1, 0))

    def debug2(self):
        if self.currentRoom != None:
            print("- 层级瓦片实体测试 -")
            for tile in self.currentRoom.currentLayerEntity.tiles:
                print(tile.cpos, tile.roomName, tile.layerName)

    def debug3(self):
        '''快照信息测试'''

        print(self.currentRoom.currentLayerEntity.snapshots)

    def exportRoomImage(self):
        '''导出房间预览图测试'''

        pixmap = self.roomList.firstRoom().exportPixmap()
        pixmap.save("./output.png", "PNG")

    def setup(self):
        '''把所有控件添加到EuclidWindow'''

        _func = lambda x: QSize(120, max(x.height() - 50, 100))
        self.roomList = RoomList(self.onMoveRoom, self.onAdjustRoom, self.onRoomDelete, self.onRoomVisibleChanged, self.onCreateRoom, self.onRoomChoozed, _func, minsize=(120, 100))
        self.add(self.roomList)

        _func = lambda x: QSize(90, max(x.height() - 50, 100))
        self.layerList = LayerList(self.onLayerDeleted, self.onLayerChoosed, _func, minsize=(90, 100))
        self.addh(self.layerList)

        _func = lambda x: QSize(x.width() - 235, max(x.height() - 50, 100))
        c = self.addh_container(_func, minsize=(100, 100), has_border=False)

        self.statusIndicator = EuclidMiniIndicator()
        c.add(self.statusIndicator)
        self.statusIndicator.invalid()
        self.statusLabel = EuclidLabel(text="工程空置", size=(200, 14))
        c.addh(self.statusLabel)
        c.addh(EuclidLabel(size=(5, 14), text="|"))
        self.info = EuclidLabel(size=(320, 14))
        self.info.success("编辑器已经初始化完成..")
        c.addh(self.info)
        _func = lambda s: QSize(s.width(), s.height() - 17)
        c.add(EuclidElasticDocker(_func, self.rendererView, size=(100, 86)))

        createBtn = EuclidButton(title="创建新的副本", callback=lambda:self.questionSave(self._createNewInstance))
        restyle(createBtn, EuclidNames.BUTTON_RED)
        self.add(createBtn)

        self.addh(EuclidButton(size=(120, 20), title="层级瓦片数据测试", callback=self.debug))
        self.addh(EuclidButton(size=(120, 20), title="层级瓦片实体测试", callback=self.debug2))
        self.addh(EuclidButton(size=(80, 20), title="图层快照测试", callback=self.debug3))
        self.addh(EuclidButton(size=(80, 20), title="导出测试", callback=self.exportRoomImage))

class Layer:
    '''记录一个图层的所有数据'''

    def __init__(self, roomName, name, cpos, csize, index):
        self.roomName = roomName
        self.cpos = cpos
        self.name = name
        self.tilemap = Tilemap(csize)
        self.tiles = list()
        self.index = index
        self.visible = True
        self.selectable = False
        self.sEntryPoint = QPointF(*cpos) * UNITSIZE
        self.snapshots = collections.deque(list(), Editor.SNAPSHOT_CAPACITY)
        self.hasChanged = False
        self.currentSnapshot = LayerSnapshot(self)

    def toJson(self) -> dict:
        '''转换为json数据以备保存'''

        tiles = list()
        for item in self.tiles:
            # 记录所有瓦片的位置和ID
            tiles.append({"pos":item.cpos, "tileId":item.tileId})

        return {
            "name":self.name,
            "pos":self.cpos,
            "size":self.tilemap.size,
            "index":self.index,
            "tiles":tiles
        }

    def fromJsonInMapEditor(self, o, view, renderer):
        '''仅从json数据中还原所有的瓦片信息, 还原的瓦片为房间瓦片'''

        for tile in o["tiles"]:
            tileId = tile["tileId"]
            item = RoomTileItem(view, tileId, tuple(tile["pos"]), Editor.tilelut.fetchPixmap(tileId))
            item.reposOffset(self.sEntryPoint)
            renderer.addItem(item)
            self.addTile(item)
            self.tilemap.data[item.cpos[0]:item.cpos[0] + item.size[0], item.cpos[1]:item.cpos[1] + item.size[1]] = item.narr

    def fromJsonAsTemplate(self, o):
        '''将层级视为模板层级来还原'''

        for tile in o["tiles"]:
            tileId = tile["tileId"]
            tileInfo = Editor.tilelut.fetch(tileId)
            model = TileModel(tileId, tuple(tile["pos"]), tileInfo.pixmap)
            self.tiles.append(model)
            self.tilemap.data[model.cpos[0]:model.cpos[0] + tileInfo.size[1], model.cpos[1]:model.cpos[1] + tileInfo.size[1]] = tileInfo.narr

    def removeSnapshotsNeedTile(self, tileId):
        '''移除需要目标瓦片Id的层级快照'''

        recycle = list()
        for snapshot in self.snapshots:
            if snapshot.needTile(tileId):
                recycle.append(snapshot)
        for s in recycle:
            self.snapshots.remove(s)

    def clearSnapshots(self):
        '''房间大小重新调整时, snapshot必须清零'''
        self.snapshots.clear()

    def restoreSnapshot(self, view, renderer):
        if len(self.snapshots) > 0:
            print("恢复前一帧的快照")
            _snapshot = self.snapshots.pop()
            _snapshot.restore(self, view, self.sEntryPoint, renderer)
            self.currentSnapshot = LayerSnapshot(self)

    def saveSnapshot(self):
        '''当图层数据发生改变时才会记录'''

        self.snapshots.append(self.currentSnapshot)
        self.currentSnapshot = LayerSnapshot(self)
        print(f"记录当前快照{len(self.snapshots)}")

    def saveSnapshotWhenChanged(self):
        '''仅在发生数据改变之后再保存快照'''

        if self.hasChanged:
            self.saveSnapshot()
            self.hasChanged = False

    def isEmpty(self):
        '''检查当前的图层是否是一个空图层'''
        return len(self.tiles) == 0

    def needTile(self, tileId):
        '''检查数据中是否用到了目标瓦片'''
        return np.any(self.tilemap.data == tileId)

    def clone(self, csize):
        '''克隆出一个自身的副本'''

        _clone = Layer(self.roomName, self.name, self.cpos, csize, self.index)
        _clone.tilemap = self.tilemap.clone()
        for tile in self.tiles:
            model = TileModel(tile.tileId, tile.cpos, tile.pixmap())
            _clone.tiles.append(model)
        return _clone

    def adjust(self, csize:tuple, lb:tuple, rt:tuple):
        '''调整当前层级的范围 '''

        narr = self.tilemap.data[lb[0]:rt[0], lb[1]:rt[1]]          # 截取需要的数据部分
        self.tilemap = Tilemap(csize)
        self.tilemap.data[:rt[0] - lb[0], :rt[1] - lb[1]] = narr

    def addTile(self, tile: RoomTileItem):
        '''添加一块瓦片'''

        tile.roomName = self.roomName
        tile.layerName = self.name
        tile.setZValue(-self.index)
        tile.lastPos += self.sEntryPoint
        self.tiles.append(tile)
        self.hasChanged = True

    def removeTile(self, tile: RoomTileItem):
        '''移除一块瓦片'''

        self.tiles.remove(tile)
        self.hasChanged = True

    def setLayerName(self, name):
        '''重设层级名称'''

        self.name = name
        for tile in self.tiles:
            tile.layerName = name

    def setLayerIndex(self, index):
        '''重设层级的Z值'''

        self.index = index
        for tile in self.tiles:
            tile.setZValue(-index)

    def setRoomName(self, name):
        self.roomName = name
        for tile in self.tiles:
            tile.roomName = name

    def changeVisible(self):
        '''重设当前图层是否可见'''

        self.visible = not self.visible
        if self.visible:
            for tile in self.tiles:
                tile.show()
        else:
            for tile in self.tiles:
                tile.hide()
        return self.visible

    def setVisible(self, value):
        '''指定图层是否可见 '''

        if self.visible != value:
            self.visible = value
            if value:
                for tile in self.tiles:
                    tile.show()
            else:
                for tile in self.tiles:
                    tile.hide()

    def setLayerSelectable(self, value):
        '''设置当前图层的瓦片是否支持被选中'''

        if self.selectable != value:
            self.selectable = value
            flags = QGraphicsItem.ItemIsMovable|QGraphicsItem.ItemIsSelectable if value else QGraphicsItem.ItemIsPanel
            for tile in self.tiles:
                tile.setFlags(flags)

class Room:
    '''记录一个房间所有的数据, 主要记录的是房间的图层级, 每一个图层就是一个
    Tilemap'''

    def __init__(self, name, cpos=(0, 0), csize=(32, 32), createRoomBorder=True):
        self.name = name

        # 追加一个默认的层级
        self.currentLayer = "default"
        self.layerNames = [self.currentLayer]
        self.layers = {self.currentLayer:Layer(name, self.currentLayer, cpos, csize, 0)}
        
        # 记录位置和空间数据
        self.reloadData(cpos, csize)
        if createRoomBorder:
            self.buildBorder()
        self.visible = True

    def toJson(self):
        '''转换为JSON数据保存下来'''

        layers = []
        for name in self.layerNames:
            layers.append({"name":name, "data":self.layers[name].toJson()})
        return {
            "name":self.name,
            "pos":self.cpos,
            "size":self.csize, 
            "layers":layers
        }

    def fromJsonInMapEditor(self, o, view, renderer):
        '''从JSON数据中还原一个房间, 只读取所有的层级数据
        房间的创建需要通过上级单位来控制'''

        self.layers.clear()
        self.layerNames.clear()
        for info in o["layers"]:
            # 所有的层级信息

            name, data = info["name"], info["data"]
            layer = Layer(self.name, name, tuple(data["pos"]), tuple(data["size"]), data["index"])
            layer.fromJsonInMapEditor(data, view, renderer)
            self.layers.setdefault(name, layer)
            self.layerNames.append(name)
        renderer.addItem(self.roomBorder)

    def fromJsonAsTemplate(self, o):
        '''作为模板还原房间'''

        self.layers.clear()
        self.layerNames.clear()
        for info in o["layers"]:
            name, data = info["name"], info["data"]
            layer = Layer(self.name, name, tuple(data["pos"]), tuple(data["size"]), data["index"])
            layer.fromJsonAsTemplate(data)
            self.layers.setdefault(name, layer)
            self.layerNames.append(name)

    def checkHasSaved(self):
        '''检查当前所有的图层是否发生了变动'''

        for layer in self.layers.values():
            if not layer.tilemap.hasSaved:
                return False
        return True

    def clearSnapshots(self, Id):
        '''清除所有层级需要目标瓦片ID的层级'''
        for layer in self.layers.values():
            layer.removeSnapshotsNeedTile(Id)

    def rectRaw(self):
        '''当前房间的矩形, 只记录大小'''
        return QRectF(0, 0, self.csize[0] * UNITSIZE, self.csize[1] * UNITSIZE)

    def buildBorder(self):
        '''创建该房间自己的border'''

        self.roomBorder = QGraphicsRectItem()
        self.roomBorder.setPen(Editor.COLOR_DEFAULT_ROOMBORDER)
        self.roomBorder.setZValue(LAST)
        self.roomBorder.setRect(self.cpos[0] * UNITSIZE, self.cpos[1] * UNITSIZE, self.csize[0] * UNITSIZE, self.csize[1] * UNITSIZE)

    def isEmptyRoom(self):
        '''检查当前房间是否是一个空房间'''

        for layer in self.layers.values():
            if layer.isEmpty():
                return True
        return False

    def exportPixmap(self) -> QPixmap:
        '''将房间导出为一张QPixmap数据'''

        box = QPixmap(QSize(*self.csize) * UNITSIZE)
        box.fill(QColor(0, 0, 0, 0))
        painter = QPainter(box)
        for name in reversed(self.layerNames):
            layer = self.layers[name]
            for tile in layer.tiles:
                pixmap = tile.pixmap()
                painter.drawPixmap(tile.getScenePosition(), pixmap)
        painter.end()
        return box        

    def needTile(self, tileId) -> bool:
        '''检查房间是否用到了目标瓦片'''

        for layer in self.layers.values():
            if layer.needTile(tileId):
                return True
        return False

    def createRoomBorder(self):
        '''创建一个房间边框'''

        item = QGraphicsRectItem()
        item.setRect(0, 0, self.csize[0] * UNITSIZE, self.csize[1] * UNITSIZE)
        item.setPen(Editor.COLOR_TEMPLATE_ROOMBORDER)
        item.setZValue(LAST)
        return item

    def clone(self):
        '''克隆出一个自身的副本'''

        room = Room(self.name, self.cpos, self.csize, createRoomBorder=False)
        room.layerNames.clear()
        room.layers.clear()
        for name in self.layerNames:
            room.layerNames.append(name)
            room.layers.setdefault(name, self.layers[name].clone(self.csize))
        return room

    def reloadData(self, cpos, csize):
        '''重设当前房间的数据'''

        self.cpos = cpos
        self.cpos2 = (cpos[0] + csize[0], cpos[1] + csize[1])
        self.csize = csize

    def adjust(self, cpos:tuple, csize:tuple, lb, rt):
        '''调整当前房间的大小信息'''

        srpos = QPointF(*cpos) * UNITSIZE
        self.reloadData(cpos, csize)
        self.roomBorder.setRect(cpos[0] * UNITSIZE, cpos[1] * UNITSIZE, csize[0] * UNITSIZE, csize[1] * UNITSIZE)
        for layer in self.layers.values():
            for tile in layer.tiles:
                tile.cpos = (tile.cpos[0] - lb[0], tile.cpos[1] - lb[1])
                tile.reposOffset(srpos)
            layer.adjust(csize, lb, rt)
            layer.cpos = cpos
            layer.sEntryPoint = srpos
            layer.clearSnapshots()

    def move(self, cpos):
        '''类似于adjust函数, 但仅移动'''

        srpos = QPointF(*cpos) * UNITSIZE
        self.reloadData(cpos, self.csize)
        self.roomBorder.setRect(self.cpos[0] * UNITSIZE, self.cpos[1] * UNITSIZE, self.csize[0] * UNITSIZE, self.csize[1] * UNITSIZE)
        for layer in self.layers.values():
            for tile in layer.tiles:
                tile.reposOffset(srpos)
            layer.cpos = cpos
            layer.sEntryPoint = srpos

    def constraint(self) -> tuple:
        '''当重新调整房间时, 应该首先计算放置房间最少需要多大的空间
        计算方式主要通过依次计算每个图层的数据, 返回所需要的空间的上下点信息'''
        
        l = self.layers[self.layerNames[0]]
        lb, rt = constraint(l.tiles)
        for name in self.layerNames[1:]:
            _lb, _rt = constraint(self.layers[name].tiles)
            lb[0] = min(lb[0], _lb[0])
            lb[1] = min(lb[1], _lb[1])
            rt[0] = max(rt[0], _rt[0])
            rt[1] = max(rt[1], _rt[1])
        return tuple(lb), tuple(rt)

    def changeVisible(self):
        self.visible = not self.visible
        for layer in self.layers.values():
            layer.changeVisible()
        return self.visible

    def normal(self):
        self.roomBorder.setPen(Editor.COLOR_DEFAULT_ROOMBORDER)

    def choosed(self):
        self.roomBorder.setPen(Editor.COLOR_CHOOSED_ROOMBORDER)

    def setRoomName(self, name):
        self.name = name
        for v in self.layers.values():
            v.setRoomName(name)

    @property
    def currentLayerRow(self):
        return self.layerNames.index(self.currentLayer)

    @property
    def currentLayerEntity(self) -> Layer:
        return self.layers[self.layerNames[self.currentLayerRow]]

    def setCurrentLayer(self, name):
        '''设置当前房间被选中的图层'''

        if self.currentLayer in self.layers:
            self.layers[self.currentLayer].setLayerSelectable(False)
        self.currentLayer = name

    def collision(self, p1, p2):
        '''检查选框是否和当前房间碰撞'''

        if p1[0] >= self.cpos2[0] or p2[0] <= self.cpos[0] or p1[1] >= self.cpos2[1] or p2[1] <= self.cpos[1]:
            return False
        return True

    def nextLayerName(self):
        count = len(self.layers)
        while 1:
            name = f"新建图层{count}"
            if name in self.layerNames:
                count += 1
                continue
            return name

    def createNewLayer(self):
        '''创建一个新的图层'''

        name = self.nextLayerName()
        self.layerNames.append(name)
        layer = Layer(self.name, name, self.cpos, self.csize, len(self.layers))
        layer.visible = self.visible
        self.layers.setdefault(name, layer)
        return name, layer.visible

class LayerList(_EuclidElasticWidget):

    def __init__(self, onItemDeleted, onItemChoosed, resizefunc, minsize=(90, 100)):
        super().__init__(resizefunc, size=minsize)
        self.title = EuclidLabel(size=(90, 14), text="- 图层列表 -", center=True)
        self.title.setParent(self)
        self.addLayerBtn = EuclidButton(size=(89, 20), title="添加图层", callback=self.addLayer)
        self.addLayerBtn.setParent(self)
        self.addLayerBtn.move(0, 19)

        self.listView = SimpleListWidget(self.onItemRenamed, onItemDeleted, self.onVisibleChanged, onItemChoosed, parent=self)
        self.listView.setObjectName("EditorBrushContainerList")
        self.listView.setGeometry(0, 44, 89, 100)
        self.currentRoom = None

    def invalid(self):
        '''禁用当前控件'''

        self.listView.setEnabled(False)
        self.addLayerBtn.invalid()

    def resume(self):
        '''恢复当前控件'''

        self.listView.setEnabled(True)
        self.addLayerBtn.resume()

    def onVisibleChanged(self, Id):
        if self.currentRoom.visible:
            return self.currentRoom.layers[Id].changeVisible()
        return False

    def _setVisible(self, value):
        for row in range(self.listView.count()):
            self.listView.itemWidget(self.listView.item(row))._setVisible(value)

    def onItemRenamed(self, Id, newId):
        if newId in self.currentRoom.layerNames:
            QMessageBox.information(None, "错误报告", "该图层ID已经存在", QMessageBox.Ok)
            return False
        else:
            # 层级名称列表
            idx = self.currentRoom.layerNames.index(Id)
            self.currentRoom.layerNames[idx] = newId
            if self.currentRoom.currentLayer == Id:
                self.currentRoom.currentLayer = newId

            # 层级实体字典
            layer = self.currentRoom.layers.pop(Id)
            layer.setLayerName(newId)
            self.currentRoom.layers[newId] = layer
            return True

    def addLayer(self):
        '''创建一个新的图层'''

        if self.currentRoom != None:
            layerName, visible = self.currentRoom.createNewLayer()
            self.listView.add(layerName)._setVisible(visible)

    def setRoom(self, room):
        '''加载目标房间并检查当前房间的状态'''

        self.currentRoom = room
        self.reloadRoom()
        self.listView.setCurrentRow(self.currentRoom.currentLayerRow)

    def reloadRoom(self):
        self.listView.clear()
        for name in self.currentRoom.layerNames:
            self.listView.add(name)
        if self.currentRoom.visible:
            # 父类是可见的，则检查图层是否可见
            for idx, name in enumerate(self.currentRoom.layerNames):
                if not self.currentRoom.layers[name].visible:
                    self.listView.itemWidget(self.listView.item(idx))._setVisible(False)
        else:
            self._setVisible(False)

    def resizeEvent(self, event) -> None:
        self.listView.resize(89, self.height() - 44)
        return super().resizeEvent(event)

class RoomList(_EuclidElasticWidget):

    def __init__(self, moveRoomCB, adjustRoomCallback, deleteRoomCallback, visibleCallback, createRoomCallback, callback, resizefunc, minsize=(110, 100)):
        super().__init__(resizefunc, size=minsize)

        self.rooms = dict()
        self.roomNames = list()
        self.title = EuclidLabel(size=(119, 14), text="- 房间列表 -", center=True)
        self.title.setParent(self)
        self.addRoomBtn = EuclidButton(size=(119, 20), title="添加房间", callback=createRoomCallback)
        self.addRoomBtn.setParent(self)
        self.addRoomBtn.move(0, 19)

        self.adjustRoomBtn = EuclidButton(size=(119, 20), title="调整房间", callback=adjustRoomCallback)
        self.adjustRoomBtn.setParent(self)
        self.adjustRoomBtn.move(0, 44)

        self.moveRoomBtn = EuclidButton(size=(119, 20), title="移动房间", callback=moveRoomCB)
        self.moveRoomBtn.setParent(self)
        self.moveRoomBtn.move(0, 69)

        self.listView = SimpleListWidget(self.onDataChanged, deleteRoomCallback, self.onVisibleChanged, self.onItemClicked, parent=self)
        self.listView.setObjectName("EditorBrushContainerList")
        self.listView.setGeometry(0, 94, 119, 100)

        self.callback = callback                                    # 选中房间时, 执行该函数回调
        self.visibleCB = visibleCallback
        self.isValid = False
        self.invalid()

    def clearSnapshots(self, Id):
        '''清除目标房间中所有需要目标ID的快照'''
        for room in self.rooms.values():
            room.clearSnapshots(Id)

    def invalid(self):
        '''禁用当前的控件'''

        self.addRoomBtn.invalid()
        self.adjustRoomBtn.invalid()
        self.moveRoomBtn.invalid()
        self.listView.setEnabled(False)

    def resume(self):
        '''恢复当前的控件'''

        self.addRoomBtn.resume()
        self.adjustRoomBtn.resume()
        self.moveRoomBtn.resume()
        self.listView.setEnabled(True)

    def firstRoom(self) -> Room:
        return self.rooms[self.roomNames[0]]

    def removeRoom(self, roomName, renderer:QGraphicsScene):
        '''移除房间 '''

        self.listView.takeItem(self.roomNames.index(roomName))
        self.roomNames.remove(roomName)
        room = self.rooms.pop(roomName)
        for layer in room.layers.values():
            for tile in layer.tiles:
                renderer.removeItem(tile)
        renderer.removeItem(room.roomBorder)

    def collisionAny(self, p1, p2)->bool:
        '''检查新框选的房间是否和任何一个房间冲突'''

        for r in self.rooms.values():
            if r.collision(p1, p2):
                return True
        return False

    def collisionExcept(self, name, p1, p2):
        '''检查新框选的房间是否和除了该房间之外的任何其他房间冲突'''

        for r in self.rooms.values():
            if r.name != name:
                if r.collision(p1, p2):
                    return True
        return False  

    def setRooms(self, rooms):
        self.rooms = rooms
        self.listView.clear()
        self.roomNames.clear()
        for name in rooms.keys():
            self.roomNames.append(name)
            self.listView.add(name)
        self.isValid = True

    def onVisibleChanged(self, Id):
        v = self.rooms[Id].changeVisible()
        self.visibleCB(Id, v)
        return v

    def onDataChanged(self, Id, newId):

        if newId in self.rooms:
            QMessageBox.information(None, "错误报告", "该房间ID已经存在", QMessageBox.Ok)
            return False
        else:
            room = self.rooms.pop(Id)
            room.name = newId
            self.rooms.setdefault(newId, room)
            for layer in room.layers.values():
                layer.setRoomName(newId)
            Editor.roomHandler.onRoomChoosed(room)
            return True

    def onItemClicked(self, Id):
        self.callback(self.rooms[Id])

    def nextRoomName(self):
        '''获得一个新的房间名'''

        count = len(self.rooms)
        while 1:
            roomName = f"新建房间{count}"
            if roomName in self.rooms:
                count += 1
                continue
            return roomName

    def createRoom(self, cpos, csize):
        '''创建一个新的房间, 连带数据一起创建'''

        room = Room(self.nextRoomName(), cpos, csize)
        self.rooms.setdefault(room.name, room)
        self.roomNames.append(room.name)
        self.listView.add(room.name)
        self._rechoose()
        return room

    def restoreRoom(self, cpos, room, sceneView, renderer):
        '''从模板中还原的房间 '''

        _room = Room(self.nextRoomName(), cpos, room.csize)
        self.rooms.setdefault(_room.name, _room)
        self.roomNames.append(_room.name)
        self.listView.add(_room.name)
        self._rechoose()

        # 写入当前模板的瓦片数据
        _room.layers.clear()
        _room.layerNames.clear()
        offset = QPointF(*cpos) * UNITSIZE
        for idx, name in enumerate(room.layerNames):
            layer = room.layers[name]
            _room.layerNames.append(name)
            _layer = Layer(_room.name, name, cpos, room.csize, idx)
            _room.layers.setdefault(name, _layer)
            for tile in layer.tiles:
                item = tile.createRoomItem(sceneView, offset)
                _layer.addTile(item)
                renderer.addItem(item)
            _layer.tilemap = layer.tilemap.clone()
        renderer.addItem(_room.roomBorder)
        return _room

    def _rechoose(self):
        if self.listView.count() == 1:
            self.listView.setCurrentRow(0)
        else:
            self.listView.setCurrentRow(self.listView.currentIndex().row())

    def resizeEvent(self, event) -> None:
        self.listView.resize(119, self.height() - 94)
        return super().resizeEvent(event)

class Editor:
    '''编辑器所有主要单元'''

    ALPHA = QColor(0, 0, 0, 0)

    PROJECT_TEMP = "./.project"
    PROJECT_TEMP_TILELUT_PATH = "./.project/tilelut.zip"
    PROJECT_TEMP_PROJECT = "./.project/pj.json"

    SNAPSHOT_CAPACITY = 20

    # 所有基础配置
    COLOR_DEFAULT_ROOMBORDER = QColor("#74adbb")
    COLOR_CHOOSED_ROOMBORDER = QColor("#66ffe3")
    COLOR_TEMPLATE_ROOMBORDER = QColor("#ffffe4")

    comicFont = QFont("Zpix")
    tilelut = TileLut()                             # 瓦片查找表
    brushMaker = BrushMaker()                       # 笔刷生成器
    cursor = QCursor()
    
    # 需要创建的所有窗体单元
    palette = None                                  # 调色盘
    brushObserver = None                            # 笔刷观察器
    brushWindow = None
    mapEditor = None
    mapEditorPreview = None
    roomHandler = None
    roomCreatorHelper = None

    # 其他子单元
    brushContainer = None                           # 笔刷组渲染器
    brushList = None                                # 笔刷组列表

    @staticmethod
    def exportMapData():
        '''导出地图数据'''

        try:
            path, t = QFileDialog.getSaveFileName(None, "选择导出位置", filter="JSON文件(*.json)")
            if len(path) > 0:
                data = Editor.mapEditor.exportMapData()
                if data != None:
                    with open(path, "w", encoding='utf-8') as f:
                        json.dump(data, f)
                    warning("导出地图数据", "导出成功!")
        except Exception as e:
            warning("导出失败", f"遇到异常:{e}")

    @staticmethod
    def loadTileLut(filepath):
        '''加载瓦片查找表'''

        # 提取所有的文件到本地文件夹
        folder = "./tmp"
        zfile = zipfile.ZipFile(filepath)
        zfile.extractall(folder)

        path = f"{folder}/lut.json"
        if os.path.exists(path):
            ret = False
            with open(path, "r", encoding='utf-8') as f:
                lut = json.load(f)
                Editor.tilelut = TileLut()
                if Editor.tilelut.loadFromLut(lut, folder):
                    Editor.brushWindow.loadTileBrushes(Editor.tilelut.generateBrushes())
                    ret = True
                else:
                    warning("创建副本", "无效的查找表文件")
            zfile.close()
            removeFolder(folder)
            # 将目标位置的瓦片查找表复制到本地, 以备保存工程文件
            if filepath != Editor.PROJECT_TEMP_TILELUT_PATH:
                shutil.copyfile(filepath, Editor.PROJECT_TEMP_TILELUT_PATH)
            return ret
        else:
            zfile.close()
            warning("创建副本", "无效的查找表文件")
            return False

    @staticmethod
    def saveProject():
        '''保存当前的工程'''

        filepath, filetype = QFileDialog.getSaveFileName(None, "选择要保存的位置", filter="ZIP文件(*.zip)")
        if len(filepath) > 0:
            o = {
                "brushList":Editor.brushWindow.toJson(),
                "roomList":Editor.mapEditor.toJson(),
                "templateList":Editor.roomHandler.toJson()
            }
            with open(Editor.PROJECT_TEMP_PROJECT, "w", encoding='utf-8') as f:
                json.dump(o, f, ensure_ascii=False)
            zfile = zipfile.ZipFile(filepath, "w")
            zfile.write(Editor.PROJECT_TEMP_TILELUT_PATH, "tilelut.zip")
            zfile.write(Editor.PROJECT_TEMP_PROJECT, "pj.json")
            zfile.close()

    @staticmethod
    def loadProject():
        '''加载工程, 优先查看当前编辑器是否有未保存的工程'''

        Editor.mapEditor.questionSave(Editor._loadProject)

    @staticmethod
    def _loadProject():
        '''加载工程到当前编辑器'''

        filepath, filetype = QFileDialog.getOpenFileName(None, "选择工程文件", filter="ZIP文件(*.zip)")
        if len(filepath) > 0:
            try:
                removeFolder(Editor.PROJECT_TEMP, False)
                zfile = zipfile.ZipFile(filepath)
                zfile.extractall(Editor.PROJECT_TEMP)
                if Editor.loadTileLut(Editor.PROJECT_TEMP_TILELUT_PATH):
                    with open(Editor.PROJECT_TEMP_PROJECT, "r", encoding='utf-8') as f:
                        pj = json.load(f)
                        Editor.brushWindow.fromJson(pj["brushList"])
                        Editor.mapEditor.fromJson(pj["roomList"])
                        Editor.roomHandler.fromJson(pj["templateList"])
                        Editor.resumeAll()
                else:
                    warning("加载错误", "瓦片查找表损坏")
                zfile.close()
            except Exception as e:
                warning("加载错误", f"无效的工程文件:{e}")

    @staticmethod
    def invalidAll():
        '''禁用当前跟工程数据有关的窗体, 在没有创建工程时, 这些窗体无法使用
        1.笔刷窗体
        2.模板窗体
        3.地图编辑器 '''

        Editor.brushWindow.invalid()
        Editor.roomHandler.invalid()
        Editor.mapEditor.invalid()

    @staticmethod
    def resumeAll():
        '''在工程创建时，恢复当前窗体'''

        Editor.brushWindow.resume()
        Editor.roomHandler.resume()
        Editor.mapEditor.resume()

    @staticmethod
    def recordSnapshot():
        '''给当前的图层记录一帧快照'''

        room = Editor.mapEditor.currentRoom
        if room != None:
            room.currentLayerEntity.saveSnapshot()

    @staticmethod
    def recordSnapshotWhenChanged():
        room = Editor.mapEditor.currentRoom
        if room != None:
            room.currentLayerEntity.saveSnapshotWhenChanged()

    @staticmethod
    def removeTile(tileId:int) -> bool:
        '''删除目标瓦片'''

        if Editor.brushWindow.brushBoxList.needTile(tileId):
            warning("删除瓦片", "删除失败, 该瓦片被其他笔刷占用")
            return False
        if Editor.palette.needTile(tileId):
            warning("删除瓦片", "删除失败, 该瓦片被调色盘占用")
            return False
        if Editor.mapEditor.needTile(tileId):
            warning("删除瓦片", "删除失败, 该瓦片被地图编辑器占用")
            return False
        if Editor.roomHandler.needTile(tileId):
            warning("删除瓦片", "删除失败, 该瓦片被房间模板占用")
            return False
        
        Editor.mapEditor.roomList.clearSnapshots(tileId)
        Editor.tilelut._removeTile(tileId)
        return True

    @staticmethod
    def onBrushChanged(brush):
        '''回调函数, 当笔刷重设时, 该函数会被执行'''

        Editor.brushObserver.showBrush(brush)
        Editor.palette.brushTool.setBrush(brush)
        Editor.mapEditor.brushTool.setBrush(brush)
        Editor.mapEditor.floodFillTool.setBrush(brush)

    @staticmethod
    def onBrushClear():
        '''回调函数, 当笔刷被删除时, 该函数会执行'''

        Editor.brushObserver.clearBrush()
        Editor.palette.brushTool.clearBrush()
        Editor.mapEditor.brushTool.clearBrush()
        Editor.mapEditor.floodFillTool.clearBrush()

    @staticmethod
    def create(parent=None):

        Editor.palette = EditorPalette(parent=parent, paletteCanvasSize=(40, 20))
        Editor.brushObserver = EditorBrushObserver(parent=parent)
        Editor.brushWindow = EditorBrushWindow(parent=parent)
        Editor.mapEditor = MapEditor(parent=parent)
        Editor.mapEditorPreview = MapEditorRuntimePreviewWindow(Editor.mapEditor.renderer, parent=parent)
        Editor.roomHandler = RoomHandlerWindow(parent)
        Editor.roomCreatorHelper = Editor.mapEditor.createRoomCreatorHelper(parent)

        Editor.brushContainer = Editor.brushWindow.brushBoxRenderer
        Editor.brushList = Editor.brushWindow.brushBoxList

    @staticmethod
    def getMousePosition(view: EuclidView):
        return view.mapFromGlobal(Editor.cursor.pos())

    @staticmethod
    def createTextItem(txt:str):
        item = QGraphicsTextItem(txt)
        item.setFont(Editor.comicFont)
        return item

    @staticmethod
    def createApplication():

        app = QApplication(sys.argv)
        font = QFont("zpix", 9)
        font.setStyleStrategy(QFont.NoAntialias)
        app.setFont(font)
        QFontDatabase.addApplicationFont("./fonts/pixel.ttf")
        with open("./res/editorstyle.qss", encoding='utf-8') as f:
            app.setStyleSheet(f"{EUCLID_DEFAULT_STYLE}\n{f.read()}")
        return app

class Window(QMainWindow):

    def __init__(self):
        super().__init__(None)
        self.setWindowTitle(f"地图编辑器_{EDITOR_VERSION}")
        self.setObjectName("EuclidBaseWindow")
        self.resize(int(1308*0.8), int(1120*0.8))
        self.build()
        self.buildMenu()
        self.show()

    def buildMenu(self):
        '''构建主窗体菜单'''

        self.menuBar = self.menuBar()
        fileMenu = self.menuBar.addMenu("文件")
        openAct = fileMenu.addAction("打开工程")
        openAct.triggered.connect(Editor.loadProject)
        saveAct = fileMenu.addAction("保存工程")
        saveAct.triggered.connect(Editor.saveProject)
        exportMapData = fileMenu.addAction("导出地图数据")
        exportMapData.triggered.connect(Editor.exportMapData)

        viewMenu = self.menuBar.addMenu("窗口")
        showBrush = viewMenu.addAction("笔刷窗口")
        showBrush.triggered.connect(Editor.brushWindow.show)
        showPalette = viewMenu.addAction("调色盘窗口")
        showPalette.triggered.connect(Editor.palette.show)
        showMapEditor = viewMenu.addAction("地图编辑窗口")
        showMapEditor.triggered.connect(Editor.mapEditor.show)
        showTemplate = viewMenu.addAction("模板窗口")
        showTemplate.triggered.connect(Editor.roomHandler.show)
        showPreview = viewMenu.addAction("地图预览窗口")
        showPreview.triggered.connect(Editor.mapEditorPreview.show)

        testMenu = self.menuBar.addMenu("测试")
        testAct1 = testMenu.addAction("测试_保存工程")
        testAct1.triggered.connect(Editor.saveProject)
        testAct2 = testMenu.addAction("测试_打开工程")
        testAct2.triggered.connect(Editor.loadProject)

    def build(self):
        
        Editor.create(self)
        Editor.invalidAll()
        restore_window_status(self, "./res/test.json")

    def test(self):
        dialog = EuclidMessageBox()
        dialog.exec()

    def closeEvent(self, evt):
        store_window_status(self, EuclidWindow.window_list, "./res/test.json")
        if not Editor.mapEditor.checkHasSaved():
            Editor.mapEditor.questionSave(lambda:evt.accept())

if __name__ == '__main__':
    app = Editor.createApplication()
    window = Window()
    exit(app.exec_())

