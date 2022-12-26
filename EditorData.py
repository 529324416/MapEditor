# 地图编辑器数据模块

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import utils
import qtutils
import numpy as np

# WARN> 关于瓦片
class Tile:
    '''单块瓦片数据'''

    def __init__(self, tileId:int, tileName:str, pixmap:QPixmap, filepath:str, refcount=1):
        '''初始化单块瓦片数据'''

        self.tileId = tileId
        self.tileName = tileName
        self.filepath = filepath
        self.pixmap = pixmap
        self.refcount = refcount

        # 编辑器认为瓦片可以直接作为笔刷来绘画
        self.brushdata = np.array([[tileId]])

    @property
    def json(self):
        '''将该瓦片的数据转换为JSON结构'''

        return {
            "id":self.tileId,
            "name":self.tileName,
            "filepath":self.filepath,
            "refcount":self.refcount
        }

class TileLib:
    '''描述一个瓦片库/一个瓦片库可以具有多个瓦片但每个瓦片只会有一个'''

    def __init__(self, libid, name):
        '''创建一个瓦片库'''

        self.name = name
        self.libid = libid
        self.tiles = list()
        self.tileIds = set()

    def add(self, tile:Tile) -> bool:
        '''增加瓦片数据'''

        if tile.tileId in self.tileIds:
            return False
        self.tileIds.add(tile.tileId)
        self.tiles.append(tile)
        return True

    def remove(self, index:int) -> Tile:
        '''根据给定的索引来删除瓦片数据,并返回该瓦片'''

        if index >= 0 and index < len(self.tiles):
            tile = self.tiles[index]
            tile.refcount -= 1
            self.tiles.remove(tile)
            self.tileIds.remove(tile.tileId)
            return tile
        return None

    def clear_tiles(self):
        '''所有的瓦片引用数减一,如果瓦片引用数为0,则准备删除该瓦片'''

        output = list()
        self.tileIds.clear()
        for tile in self.tiles:
            tile.refcount -= 1
            if tile.refcount == 0:
                output.append(tile)
        return output

    @property
    def render_infos(self):
        '''获取需要渲染的数据'''

        return [(_.tileName, _.pixmap) for _ in self.tiles]

class TileManager:
    '''瓦片管理器'''

    def __init__(self, tilesize=(12, 12)):
        '''管理所有的瓦片'''

        TileManager.instance = self
        self.counter = utils.Counter(entry=1)
        self.tilesize = QSize(*tilesize)

        # DOC> 瓦片名 > 瓦片实体
        self.tiles = dict()

        self.libs = list()
        self.libCounter = utils.Counter(entry=1)
        self.currentlib = None
        self.hasSaved = True

    def findLib(self, name) -> tuple:
        '''根据名称找到目标库'''

        for i, lib in enumerate(self.libs):
            if lib.name == name:
                return i, lib
        return -1, None

    def indexLib(self, index:int) -> TileLib:
        '''根据索引找到一个库'''

        if index >= 0 and index < len(self.libs):
            return self.libs[index]
        return None

    def set_current_lib(self, name:str) -> TileLib:
        '''设置当前的瓦片库'''

        index, lib = self.findLib(name)
        if lib != None:
            self.currentlib = lib
            return self.currentlib
        return None

    def createLib(self):
        '''新建一个瓦片的库/该库会成为当前被选中的库'''

        libid = self.libCounter.next_id
        name = f"新建库{libid}"
        self.currentlib = TileLib(libid, name)
        self.libs.append(self.currentlib)
        return self.currentlib

    def removeLib(self, index):
        '''删除目标瓦片库'''

        lib = self.libs[index]
        tiles = lib.clear_tiles()
        self.libCounter.recycle(lib.libid)
        self.libs.remove(lib)

        for tile in tiles:
            self.tiles.pop(tile.tileName)
            self.counter.recycle(tile.tileId)

    def removeTile(self, tile: Tile):
        '''删除单块瓦片\n
        检查是否有地图数据引用了这块瓦片,如果有则不予删除'''

        # TODO> 检查是否有地图或者笔刷数据引用了这块瓦片
        self.counter.recycle(tile.tileId)
        self.tiles.pop(tile.tileName)
        # self.tilesById.pop(tile.tileId)

    def create(self, file:str):
        '''根据给定的文件创建一个新的瓦片数据'''

        if file is None or not os.path.exists(file):
            return False
        try:
            name = utils.parseNameFromPath(file)
            if name in self.tiles:
                tile = self.tiles[name]
                tile.refcount += 1
                self.currentlib.add(tile)
                return True
            pixmap = QPixmap(file)
            if pixmap.size() != self.tilesize:
                return False
            tile = Tile(self.counter.next_id, name, pixmap, file)
            self.tiles.setdefault(tile.tileName, tile)
            # self.tilesById.setdefault(tile.tileId, tile)
            self.currentlib.add(tile)
            return True
        except:
            return False

    def _import_tiles(self) -> list:
        '''导入一组瓦片'''
        
        self.hasSaved = False
        failed_list = []
        filenames = qtutils.openfiles(caption="选择瓦片")
        if filenames is None:
            return False, None
        for filename in filenames:
            if not self.create(filename):
                failed_list.append(filename)
        return True, failed_list

    @property
    def json(self):
        '''将所有的瓦片转换为一个JSON数据,它将以查找表的形式存在,通过瓦片Id查找瓦片名称,并且该数据还会记录自身的回收列表情况'''

        tiles = {
            "counter":self.counter.json,
            "tiles":[v.json for v in self.tiles.values()]
        }
        _libs = dict()
        for lib in self.libs:
            _libs.setdefault(lib.name, {"tiles":[_.tileId for _ in lib.tiles],"libId":lib.libid})
        return {
            "tiles":tiles,
            "libs":{
                "counter":self.libCounter.json,
                "libs":_libs
            }
        }

    def load_json(self, obj: dict) -> int:
        '''从json数据中恢复当前的tileManager'''

        jsonTile = obj["tiles"]
        missingCount = 0
        self.counter.load_json(jsonTile["counter"])
        namelut = dict()
        for tileinfo in jsonTile["tiles"]:
            try:
                pixmap = QPixmap(tileinfo["filepath"])
                tmp = Tile(tileinfo["id"], tileinfo["name"], pixmap, tileinfo["filepath"], tileinfo["refcount"])
                self.tiles.setdefault(tmp.tileName, tmp)
                namelut.setdefault(tmp.tileId, tmp.tileName)
            except:
                missingCount += 1

        jsonLib = obj["libs"]
        self.libCounter.load_json(jsonLib["counter"])
        for name, lib in jsonLib["libs"].items():
            tmp = TileLib(lib["libId"], name)
            for tileId in lib["tiles"]:
                tile = self.tiles.get(namelut[tileId])
                if tile != None:
                    tmp.add(tile)
            self.libs.append(tmp)
            self.currentlib = tmp
        return missingCount
            




# class Tilemap:
#     '''一个地图层级信息/也可以直接视为层级数据'''

#     def __init__(self, name, size):
#         '''创建一个新的Tilemap'''

#         self.name = name
#         self.data = np.zeros(size, dtype=np.int32)

#     def draw(self, data: np.ndarray, pos: QPoint):
#         '''绘制一块区域'''

#         self.data[
#             pos.x():pos.x() + data.shape[0],
#             pos.y():pos.y() + data.shape[1]
#         ] = data

#     def show(self):
#         '''打印地图数据'''

#         print(np.flip(self.data.transpose(1, 0), 0))

#     def _drawpoint(self, data: np.ndarray, pos: QPoint) -> bool:
#         '''绘制单点数据/使用该函数必须确保data的维度为1x1'''

#         x, y = pos.x(), pos.y()
#         if x >= 0 and x < self.data.shape[0]:
#             if y >= 0 and y < self.data.shape[1]:
#                 if self.data[x, y] != data:
#                     self.data[x, y] = data
#                     return True
#         return False

#     def _erasepoint(self, pos: QPoint) -> None:
#         '''擦除单点数据'''

#         self.data[pos.x(), pos.y()] = 0

# class Room:
#     '''房间信息,一个房间拥有背景/基底/支架/装饰层四个层级,依次覆盖之前的层级'''

#     def __init__(self, size:tuple) -> None:

#         self.size = size
#         self.layers = [
#             Tilemap("Background", size),
#             Tilemap("Base", size),
#             Tilemap("Scaff", size),
#             Tilemap("Decroator", size)
#         ]
#         self.currentLayer = self.layers[0]
#         self.hasSaved = False

#     def findLayer(self, name:str) -> Tilemap:
#         '''寻找一个层级'''

#         for layer in self.layers:
#             if layer.name == name:
#                 return layer
#         return None



class ProjectData(QObject):
    '''工程文件
    1.管理编辑器所有的数据信息'''

    @staticmethod
    def load_fromjson(data:dict):
        '''从json文件中恢复所有的数据'''

        tilesize = tuple(data["tilesize"])
        project = ProjectData(tilesize)
        missingCount = project.tileManager.load_json(data["tileManager"])
        return project, missingCount

    tileChoosed = pyqtSignal(Tile)
    tileRemoved = pyqtSignal(Tile)

    def __init__(self, tilesize=(12, 12)):
        '''创建所有的数据单位'''

        super().__init__(None)
        self.tilesize = tilesize
        self.tilew,self.tileh = tilesize
        self.tileManager = TileManager(tilesize)

        self.__current_tile = None

    def choosetile(self, index:int):
        '''当用户在瓦片窗口选中了某个瓦片时执行该函数'''

        lib = self.tileManager.currentlib
        self.__current_tile = lib.tiles[index]
        self.tileChoosed.emit(self.__current_tile)

    def removetile(self, index:int) -> list:
        '''当某个瓦片被删除时执行该函数,返回被删除瓦片所在库的渲染信息'''

        lib = self.tileManager.currentlib
        tile = lib.remove(index)
        if tile.refcount == 0:
            if tile is self.__current_tile:
                self.__current_tile = None
            self.tileManager.removeTile(tile)
            self.tileRemoved.emit(tile)
            return lib.render_infos

    @property
    def json(self):
        return {
            "tileManager":self.tileManager.json,
            "tilesize":[self.tilew, self.tileh]
        }

    @property
    def currentTile(self):
        return self.__current_tile

    @property
    def hasSaved(self):
        return False


if __name__ == '__main__':
    '''测试'''

    # import sys
    # from PyQt5.QtWidgets import *
    # app = QApplication(sys.argv)
    # manager = TileManager()
    # tile = manager.create("./Res/test.png")


    # brushManager = BrushManager()
    # print(brushManager.create_brush_fromtile(tile)._brush_id)
    # sys.exit(app.exec_())