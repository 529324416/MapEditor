from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

from Euclid.EuclidGraphicsView import *
from EditorTools import *
from Editor import *

class TileItem(QGraphicsPixmapItem):
    '''瓦片Item'''

    def __init__(self, tileId:int, pixmap:QPixmap):
        super().__init__(pixmap, None)
        self.tileId = tileId

    def resetTile(self, tileId:int, pixmap:QPixmap):
        '''重设tile'''

        self.tileId = tileId
        self.setPixmap(pixmap)


class TilemapBuffer:
    '''编辑时的Tilemap数据'''

    def __init__(self,name:str,size:tuple):
        '''创建一个新的TileItem索引器用于表示一个Tilemap'''

        self.name = name
        self.width,self.height = size
        self.tilemap = dict()
        for x in range(size[0]):
            for y in range(size[1]):
                self.tilemap.setdefault((x, y), None)
        self._tilemap = np.zeros(size, dtype=np.int32)

    @property
    def json(self):
        '''将层级数据转换为JSON数据,结构为'''

        output = []
        for x in range(self.width):
            for y in range(self.height):
                v = self._tilemap[x, y]
                if v != 0:output.append([x, y, int(self._tilemap[x, y])])
        return output

    def show(self):
        '''打印地图数据'''

        print(np.flip(self._tilemap.transpose(1, 0), 0))

class RoomBuffer:
    '''编辑时房间数据'''

    def __init__(self, size:tuple):
        '''创建一个新的房间数据'''

        self.size = size
        self.width, self.height = size
        self.layers = {}
        self.layers.setdefault("Background",TilemapBuffer("Background", size))
        self.layers.setdefault("Base", TilemapBuffer("Base", size))
        self.layers.setdefault("Scaff", TilemapBuffer("Scaff", size))
        self.layers.setdefault("Decorator", TilemapBuffer("Decorator", size))
        self.__saved = False

    @property
    def json(self):
        '''将房间数据转换为JSON数据'''

        layers = dict()
        for name, value in self.layers.items():
            layers.setdefault(name, value.json)
        return {
            "size":[self.width, self.height],
            "layers":layers
        }

    @property
    def hasSaved(self):
        return self.__saved

class RoomDrawingBuffer:
    '''保存一组房间渲染数据,当保存该数据时,会将其写入到房间管理器,在编辑状态时,只与该房间交互
    该数据并不是常驻数据,当需要一个新的drawingBuffer的时候直接重新创建即可'''

    def __init__(self, tilesize:tuple, sourceRect:QRectF, roomtilesize, roomtilepos, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        '''存储一组房间的渲染数据
        @param tilesize 瓦片大小
        @param sourceRect 房间原始的RectF'''

        self.tilesize = tilesize
        self.room = RoomBuffer(roomtilesize)

        self.sourceRect = sourceRect

        self.roomScenePos = QPointF(roomtilepos[0] * tilesize[0], roomtilepos[1] * tilesize[1])
        self.roomPoint = QPoint(*roomtilepos)
        self.roomPointMinusOne = self.roomPoint
        self.roomPointMinusOne.setY(self.roomPoint.y() - 1)

        self.view = view
        self.scene = scene
        self.helper = helper

        self.layers = dict()
        idx = 0
        for k in self.room.layers:
            layer = QGraphicsItemGroup()
            self.layers.setdefault(k, layer)
            self.scene.addItem(layer)
            layer.setZValue(idx)
            idx += 1

        self.border = helper.createbox(EditorColor.EYECATCH_COLOR_CYAN, style=Qt.DashLine)
        self.border.setRect(self.sourceRect)
        self.scene.addItem(self.border)
        self.sourceRect.setWidth(self.sourceRect.width() - self.tilesize[0])
        self.sourceRect.setY(self.sourceRect.y() - self.tilesize[1])


        # DOC> 编辑时临时数据信息
        self.current_tile = None
        self.__current_tilemap = None
        self.__current_group = None
        self.__layer_choosed = False
        self.__copied_data = None

    def _show_current_mapdata(self):
        '''打印现在的地图数据信息'''

        if self.__layer_choosed:
            self.__current_tilemap.show()

    def abspos2relative(self, gridpos_abs:QPoint) -> tuple:
        '''根据给定的gridpos来计算真正的地图pos'''
        pos = gridpos_abs - self.roomPointMinusOne
        return pos.x(),-pos.y()

    def relativepos2abs(self, gridpos_relative:QPointF) -> QPoint:
        '''根据给定的相对坐标计算出绝对坐标'''

        gridpos_relative.setY(-gridpos_relative.y())
        return gridpos_relative + self.roomPointMinusOne

    def _force_draw_point(self, pos:tuple, scenepos:QPointF, tile_info:tuple):
        '''强制在某个点绘制一块瓦片'''

        data = self.__current_tilemap.tilemap[pos]
        tileId, pixmap = tile_info
        if data is None:
            item = TileItem(tileId, pixmap)
            item.setPos(scenepos)
            self.__current_tilemap.tilemap[pos] = item
            self.__current_tilemap._tilemap[pos[0], pos[1]] = tileId
            self.__current_group.addToGroup(item)
        elif data.tileId != tileId:
            self.__current_tilemap._tilemap[pos[0], pos[1]] = tileId
            data.resetTile(tileId, pixmap)

    def _force_erase_point(self, pos:tuple):
        '''强制擦除一个点的数据'''

        data = self.__current_tilemap.tilemap[pos]
        if data != None:
            self.__current_tilemap.tilemap[pos] = None
            self.__current_tilemap._tilemap[pos[0], pos[1]] = 0
            self.__current_group.removeFromGroup(data)

    def clear(self):
        '''销毁当前房间的渲染数据'''

        self.scene.removeItem(self.border)
        for name,layer in self.layers.items():
            self.scene.removeItem(layer)

    def chooselayer(self, layerName:str):
        '''选择一个层级的时候执行该回调函数'''

        self.__current_tilemap = self.room.layers.get(layerName)
        if self.__current_tilemap != None:
            self.__layer_choosed = True
            self.__current_group = self.layers[layerName]

    def test_borderinroom(self, p1:tuple, p2:tuple) -> bool:
        '''给定两个点位代表一个选框,测试这个选框是否处于房间范围内'''

        if p1[0] >= 0 and p1[1] >= 0:
            if p2[0] <= self.room.size[0] and p2[1] <= self.room.size[1]:
                return True
        return False

    def test_marqueebox(self, p1: QPoint, p2: QPoint):
        '''给定两个点位代表一个选框,测试这个选框是否有效,如果有效返回一个标志位并同时返回左下角和右上角的坐标'''

        p1_x, p1_y = self.abspos2relative(p1)
        p2_x, p2_y = self.abspos2relative(p2)
        p1_y += 1;p2_y += 1
        p1 = min(p1_x, p2_x), min(p1_y, p2_y)
        p2 = max(p1_x, p2_x), max(p1_y, p2_y)
        if self.test_borderinroom(p1, p2):
                return True, p1, p2
        return False, None, None

    def try_copydata(self, p1: QPoint, p2: QPoint):
        '''启动复制工具复制选框中的数据,如果当前工具不是选框或者复制的数据无效则该函数不发动效果'''

        if self.__current_tilemap != None:
            valid, p1, p2 = self.test_marqueebox(p1, p2)
            if valid:
                npdata = np.copy(self.__current_tilemap._tilemap[p1[0]:p2[0], p1[1]:p2[1]])
                shapex,shapey = npdata.shape
                if shapex * shapey != 0:
                    # NOTE> 当复制目标区域的数据时会同时记录被框选的位置到marquee_pos
                    self.__marquee_pos = p1
                    self.__copied_data = npdata, self._try_copydata_readtiles(np.copy(npdata), p1)
                    return True, QRectF(0, 0, shapex * self.tilesize[0], shapey * self.tilesize[1])
        return False,None
 
    def _try_copydata_readtiles(self, data:np.ndarray, border_entry_point:tuple) -> dict:
        '''读取一个范围内所有存储的瓦片信息'''

        out = {}
        entrypoint = np.array(border_entry_point)
        for _pos in np.vstack(np.where(data != 0)).transpose(1,0):
            pos = tuple(_pos + entrypoint)
            item = self.__current_tilemap.tilemap[pos]
            out.setdefault(item.tileId, (item.tileId, item.pixmap()))
        return out

    def drawpoint(self, scene_pos:QPointF, grid_pos:QPoint):
        '''铅笔工具绘制回调函数'''

        if self.__layer_choosed and self.current_tile != None:
            if self.sourceRect.contains(scene_pos):
                pos = self.abspos2relative(grid_pos)
                self._force_draw_point(pos, scene_pos, self.current_tile)

    def erasepoint(self, scenepos:QPointF, gridpos:QPoint):
        '''擦除回调函数'''

        if self.__layer_choosed and self.sourceRect.contains(scenepos):
            pos = self.abspos2relative(gridpos)
            self._force_erase_point(pos)

    def readpoint(self, scenepos:QPointF, gridpos: QPoint):
        '''读取目标位置的瓦片'''

        if self.__layer_choosed and self.sourceRect.contains(scenepos):
            pos = self.abspos2relative(gridpos)
            return self.__current_tilemap.tilemap.get(pos)

    def _paste_data(self, gridpos_relative:tuple, npdata:np.ndarray, tileinfos:tuple):

        roompoint = QPointF(self.roomPoint.x() * self.tilesize[0], self.roomPoint.y() * self.tilesize[1])
        for x in range(npdata.shape[0]):
            for y in range(npdata.shape[1]):
                _gridpos_relative = x + gridpos_relative[0], y + gridpos_relative[1]
                scenepos_relative = QPointF(_gridpos_relative[0] * self.tilesize[0], -_gridpos_relative[1] * self.tilesize[1]) + roompoint
                tileId = npdata[x, y]
                if tileId == 0:
                    self._force_erase_point(_gridpos_relative)
                else:
                    self._force_draw_point(_gridpos_relative, scenepos_relative, tileinfos[tileId])

    def paste_copied_data(self, gridpos_abs_qt: QPoint) -> None:
        '''在复制工具的当前位置粘贴被复制的数据'''

        gridpos_relative_qt = self.abspos2relative(gridpos_abs_qt)
        npdata, tiledicts = self.__copied_data        
        gridpos_relative = (gridpos_relative_qt[0], gridpos_relative_qt[1] - npdata.shape[1] + 1)

        # 检查方块是否处于房间范围内
        p2 = gridpos_relative[0] + npdata.shape[0], gridpos_relative[1] + npdata.shape[1]
        if self.test_borderinroom(gridpos_relative, p2):
            self._paste_data(gridpos_relative, npdata, tiledicts)
            return True
        return False

    def move_copied_data(self, gridpos_abs_qt: QPoint) -> bool:
        '''在移动工具当前的工具清空之前的旧版数据并在新的位置绘制数据'''

        gridpos_relative_qt = self.abspos2relative(gridpos_abs_qt)
        npdata, tiledicts = self.__copied_data        
        gridpos_relative = (gridpos_relative_qt[0], gridpos_relative_qt[1] - npdata.shape[1] + 1)

        # 检查目标方块是否处于房间范围内
        p2 = gridpos_relative[0] + npdata.shape[0], gridpos_relative[1] + npdata.shape[1]
        if self.test_borderinroom(gridpos_relative, p2):
            # 优先清空之前的数据，然后复制新的数据，这么做是为了放置要复制的区域有可能与新区域产生交叉
            for x in range(npdata.shape[0]):
                for y in range(npdata.shape[1]):
                    _gridpos_relative = x + self.__marquee_pos[0], y + self.__marquee_pos[1]
                    self._force_erase_point(_gridpos_relative)
            self._paste_data(gridpos_relative, npdata, tiledicts)
            return True
        return False

    def _clear_tile_in_layer(self, tileId:int, tilemap: TilemapBuffer) -> None:
        '''删除所有为目标瓦片的瓦片'''

        source = np.copy(tilemap._tilemap)
        for _pos in np.vstack(np.where(source == tileId)).transpose(1, 0):
            pos = _pos[0], _pos[1]
            tilemap._tilemap[pos[0], pos[1]] = 0
            item = tilemap.tilemap[pos]
            tilemap.tilemap[pos] = None
            yield item

    def clear_tile(self, tileId):
        '''删除所有层级中瓦片id为目标id的瓦片'''

        if tileId == 0:return
        for layer_name,tilemap in self.room.layers.items():
            layerGroup = self.layers[layer_name]
            for item in self._clear_tile_in_layer(tileId, tilemap):
                layerGroup.removeFromGroup(item)

    def setLayerVisible(self, name:str) -> bool:
        '''set if layer visible if layer is not visible, otherwise 
        set invisible'''

        group = self.layers[name]
        group.setVisible(not group.isVisible())
        return group.isVisible()