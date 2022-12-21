# 绘制用的主窗体

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *
from Euclid.EuclidGraphicsView import *
from Editor import *
from EditorData import ProjectData, Tile
from EditorTools import *
import qtutils
import utils
import numpy as np

class TileItem(QGraphicsPixmapItem):
    '''瓦片Item'''

    def __init__(self, tileId:int, pixmap:QPixmap):
        super().__init__(pixmap, None)
        self.tileId = tileId

    def resetTile(self, tileId:int, pixmap:QPixmap):
        '''重设tile'''

        self.tileId = tileId
        self.setPixmap(pixmap)

class RoomCreatorHelper(EuclidWindow):
    '''房间创建器辅助工具'''

    def __init__(self, parent=None):
        super().__init__(parent=parent, title="创建新的房间", hasButtons=False)
        self._sizegrip.set_enabled(False)
        self.resize(400, 120)

        self.btn_cancel = EuclidButton(text="取消创建")
        self.btn_confirm = EuclidButton(text="确认创建")
        self.msg_room_tilesize = QLabel(text="tilesize:(?,?)")
        self.msg_room_sourceRect = QLabel(text="rect:?")

        self.addh(self.btn_confirm, 130, 20)
        self.addh(self.btn_cancel, 130, 20)
        self.addv(self.msg_room_tilesize, 100, 20)
        self.addh(self.msg_room_sourceRect, 250, 20)

        self.reset()
        self.roomtilesize = (0, 0)
        self.roomtilepos = (0, 0)
        self.roomsize = QSizeF()
        self.roompos = QPointF()

    @property
    def isRoomValid(self):
        return self.__is_room_valid

    def reset(self):
        '''重新房间参数'''
        self.__is_room_valid = False

    def receive(self, tilesize: QSize, tilepos: QPoint, sourceRect: QRectF):
        '''根据房间工具传递过来的rect来计算房间的属性,位置,大小(瓦片单位)'''

        self.__is_room_valid = True
        self.roomtilesize = (tilesize.width(), tilesize.height())
        self.roomtilepos = (tilepos.x(), tilepos.y())
        self.roomRect = sourceRect
        self.msg_room_tilesize.setText(f"tilesize:({tilesize.width()},{tilesize.height()})")
        self.msg_room_sourceRect.setText(f"rect:({sourceRect.x()},{sourceRect.y()},{sourceRect.width()},{sourceRect.height()})")

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

    def debug_pointstr(self,x) -> str:
        return f"({x.x()},{x.y()})"

class EditorMapWindow(EuclidWindow):
    '''用于编辑单个房间\n
    根据层级管理原则,任何被MapWindow创建的单位都由MapWindow来负责,不允许下级对象越界访问MapWindow的上级对象'''

    def __init__(self, parent=None):
        super().__init__(parent=parent, title="编辑器")
        #DOC> 创建提示符
        self.message = QLabel("消息提示符")
        self.output = lambda x: self.message.setText(x)
        self.btn_pen = EuclidButton(text="铅笔", callback=lambda:self.switch_tool(self.pentool))
        self.btn_eraser = EuclidButton(text="橡皮", callback=lambda:self.switch_tool(self.erasertool))
        self.btn_marquee = EuclidButton(text="选框", callback=lambda:self.switch_tool(self.marqueetool))
        
        #DOC> 创建GraphicsView和GraphicsScene
        self.view = EditorView()
        self.view.onClicked.connect(self.onClick)
        self.view.onMove.connect(self.onMove)
        self.view.onRelease.connect(self.onRelease)
        self.view.onLeave.connect(self.onLeave)
        self.view.onEnter.connect(self.onEnter)

        #DOC> 创建LayerList和Button
        self.layerList = EditorListBox()
        self.layerList.elemClicked.connect(self.on_layerList_elemClicked)
        self.layerList.elemButtonClicked.connect(self.on_layerList_elemBtnClicked)
        self.btn_createroom = EuclidButton(text="新建房间", callback=self.trycreateroom)
        self.btn_showmarquee = EuclidButton(text="导出地图数据", callback=self.printmarqueedata)
        self.btn_testbtn = EuclidButton(text="打印地图数据", callback=self.printroomdata)
        
        #DOC> 建立布局
        self.addh(self.message, 150, 20)
        self.addh(self.btn_pen, 50, 20)
        self.addh(self.btn_eraser, 50, 20)
        self.addh(self.btn_marquee, 50, 20)
        self.addv_calch(self.layerList, 80, (1.0, -60))
        self.addh_calc(self.view, (1.0, -90), (1.0, -60))
        self.addv(self.btn_createroom)
        self.addh(self.btn_testbtn)
        self.addh(self.btn_showmarquee)

        #DOC> 其他初始化设置
        self.disable()
        self.tool = None
        self._lst_tool = None
        self.project = None
        self.roomBuffer = None
        self.scene_label = QGraphicsTextItem("hello world")
        self.scene_label.setDefaultTextColor(EditorColor.TEXT_COLOR)

    def initproject(self, project: ProjectData):
        '''根据给定的工程文件来初始化GraphicsScene'''

        self.project = project
        self.scene = EuclidSceneGrid(
            ltcolor=EditorColor.BACKGROUND_COLOR_LEVEL1, 
            hvcolor=EditorColor.BACKGROUND_COLOR_LEVEL2, 
            cellsize=(project.tilew, project.tileh)
        )
        self.view.setScene(self.scene)
        self.create_tools(self.view, self.scene, project)
        self.enable()

    # WARN> 关于绘图工具
    def create_tools(self, view: EditorView, scene: EuclidSceneGrid, projectData: ProjectData):
        '''创建所有的工具'''

        self.helper = ToolHelper(projectData.tilesize)        
        self.emptyTool = EmptyTool(view, scene, self.helper)
        self.pentool = PenTool(view, scene, self.helper)
        self.erasertool = EraserTool(view, scene, self.helper)
        self.marqueetool = MarqueeTool(view, scene, self.helper)
        self.copytool = CopyTool(view, scene, self.helper)
        self.pickertool = TilePickerTool(view, scene, self.helper)
        self.movetool = MoveTool(view, scene, self.helper)

        # DOC> 房间创建器
        self.roomTool = RoomCreatorTool(view, scene, self.helper)
        self.roomhelper = RoomCreatorHelper(parent=self.parent())
        self.roomhelper.btn_cancel.set_callback(self.cancelcreateroom)
        self.roomhelper.btn_confirm.set_callback(self.confirm_create_room)
        EuclidWindow.setOnTop(self.roomhelper)
        self.roomhelper.hide()
        self.roomTool.onSizeChanged.connect(self.roomhelper.receive)
        
    def switch_tool(self, tool: ITool, ignore_type=False) -> bool:
        '''更换当前正在使用的工具
        切换工具时会检查当前工具是否支持切换'''

        if self.roomBuffer is None or self.tool is None:
            return False
        if self.tool.canDraw or self.tool.toolType == tool.toolType:
            return False

        if self.tool.toolType >= 0 or ignore_type:
            self._lst_tool = self.tool
            self.usetool(tool)
            tool.updatePosition(self._lst_tool.indicator.pos())
            return True
        return False

    def enable(self):
        '''启用所有的部件'''
        self.message.setText("编辑器启用")
        self.view.setEnabled(True)
        self.btn_createroom.enable()
        self.btn_testbtn.enable()
        self.usetool(self.emptyTool)

    def disable(self):
        '''禁用所有部件'''
        self.message.setText("编辑器已禁用")
        self.view.setEnabled(False)
        self.btn_createroom.disable()
        self.btn_testbtn.disable()

    def usetool(self, tool):
        '''开始使用某个工具'''

        if self.tool != None:
            self.tool.stopTool()
        self.tool = tool
        self.tool.useTool()
        self.message.setText(self.tool.name)

    def trycreateroom(self):
        '''尝试创建一个新的房间'''

        if self.roomBuffer != None:
            if not self.roomBuffer.room.hasSaved:
                button = qtutils.question_withcancel(None, "创建房间","当前房间未保存,是否保存数据?")
                if button == QMessageBox.Ok:
                    self.roomBuffer.save(self.project)
                    self.roomBuffer = None
                elif button == QMessageBox.No:
                    self.roomBuffer.clear()
                elif button == QMessageBox.Cancel:
                    return
        self.btn_createroom.disable()
        self.usetool(self.roomTool)
        self.roomhelper.show()
        self.roomhelper.reset()

    def cancelcreateroom(self):
        '''取消创建新的房间'''

        self.usetool(self.emptyTool)
        self.roomhelper.hide()
        self.btn_createroom.enable()

    def confirm_create_room(self):
        '''确认创建房间'''

        #DOC> 检查数据是否有效
        if self.roomhelper.isRoomValid:
            # 开始创建房间
            self.roomBuffer = RoomDrawingBuffer(
                self.project.tilesize,
                self.roomhelper.roomRect,
                self.roomhelper.roomtilesize,
                self.roomhelper.roomtilepos,
                self.view, 
                self.scene, 
                self.helper)
            # DOC> 渲染层级信息
            self.layerList.clear()
            for name in self.roomBuffer.room.layers:
                self.layerList.add(name)
            self.layerList.clearSelection()
            self.on_project_tileChoosed(self.project.currentTile)

            # DOC> 链接所有的槽函数|所有槽函数必须在MapWindow中定义
            self.project.tileChoosed.connect(self.on_project_tileChoosed)
            self.project.tileRemoved.connect(self.on_project_tileRemoved)

            self.pentool.drawMoved.connect(self.on_pentool_drawMoved)
            self.erasertool.drawMoved.connect(self.on_erasertool_drawMoved)
            self.copytool.clicked.connect(self.on_copytool_clicked)
            self.copytool.rightClicked.connect(self.on_copytool_rightClicked)
            self.pickertool.clicked.connect(self.on_pickertool_clicked)
            self.movetool.clicked.connect(self.on_movetool_clicked)
            self.movetool.rightClicked.connect(self.on_movetool_rightClicked)

            self.cancelcreateroom()
        else:
            qtutils.information(None, "创建房间", "房间尺寸无效")

    def printroomdata(self):
        '''打印当前的房间的当前层级数据'''

        if self.roomBuffer != None:
            self.roomBuffer._show_current_mapdata()

    def printmarqueedata(self):
        '''打印选框中的数据'''

        if self.roomBuffer is None:
            qtutils.information(None, "导出地图数据", "当前没有建立房间")
        else:
            filepath = qtutils.savefile("导出地图数据")
            if filepath != None:
                obj = self.project.to_json()
                obj.setdefault("room", self.roomBuffer.room.json)
                utils.save_json(obj, filepath)

    def choose_tile(self, tileId:int, pixmap:QPixmap):
        '''分离出来主要是因为选取瓦片的方式不止从瓦片库选择一种，还可以用滴灌来选取'''

        self.pentool.tileId = tileId
        self.pentool.indicator.setPixmap(pixmap)
        self.roomBuffer.current_tile = (tileId, pixmap)

    @property
    def lastTool(self):
        return self._lst_tool if self._lst_tool != None else self.emptyTool

    # WARN> 所有的槽函数
    @pyqtSlot(Tile)
    def on_project_tileChoosed(self, tile: Tile) -> None:
        '''当瓦片被重新选择时,执行该函数'''
        if tile != None:
            self.choose_tile(tile.tileId, tile.pixmap)

    @pyqtSlot(Tile)
    def on_project_tileRemoved(self, tile: Tile) -> None:
        '''当瓦片被移除时,执行该函数'''

        if self.roomBuffer.current_tile[0] == tile.tileId:
            self.roomBuffer.current_tile = None
        if self.pentool.tileId == tile.tileId:
            self.pentool.indicator.setPixmap(self.pentool.defaultpixmap)
        self.roomBuffer.clear_tile(tile.tileId)

    @pyqtSlot(str)
    def on_layerList_elemClicked(self, name:str) -> None:
        '''当选中一个层级时执行该函数'''

        if self.roomBuffer != None:
            self.roomBuffer.chooselayer(name)

    @pyqtSlot(str)
    def on_layerList_elemBtnClicked(self, name:str) -> None:
        '''当一个层级的按钮被点击的时候'''

        if self.roomBuffer != None:
            value = self.roomBuffer.setLayerVisible(name)
            item = self.layerList.fetch(name)
            restyle(item.button, EUCLID_BUTTON if value else EUCLID_BUTTON_RED)

    @pyqtSlot(QPointF, QPoint)
    def on_pentool_drawMoved(self, scenepos:QPointF, gridpos:QPoint):
        self.roomBuffer.drawpoint(scenepos, gridpos)

    @pyqtSlot(QPointF, QPoint)
    def on_erasertool_drawMoved(self, scenepos:QPointF, gridpos:QPoint):
        self.roomBuffer.erasepoint(scenepos, gridpos)

    @pyqtSlot(QPoint)
    def on_copytool_clicked(self, gridpos:QPoint):
        self.roomBuffer.paste_copied_data(gridpos)

    @pyqtSlot()
    def on_copytool_rightClicked(self):
        self.switch_tool(self.marqueetool)

    @pyqtSlot(QPointF, QPoint)
    def on_pickertool_clicked(self, scenepos:QPointF, pos_snapped: QPoint):
        if self.roomBuffer != None:
            item = self.roomBuffer.readpoint(scenepos, pos_snapped)
            if item != None:
                self.choose_tile(item.tileId, item.pixmap())

    @pyqtSlot(QPoint)
    def on_movetool_clicked(self, gridpos: QPoint):
        '''如果成功的移动了数据就直接退出当前工具'''

        if self.roomBuffer != None:
            if self.roomBuffer.move_copied_data(gridpos):
                self.switch_tool(self.lastTool)

    @pyqtSlot()
    def on_movetool_rightClicked(self):
        if self.tool is self.movetool:
            self.switch_tool(self.lastTool)        

    def receiveKeyEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_B:
            self.switch_tool(self.pentool)
        elif event.key() == Qt.Key_E:
            self.switch_tool(self.erasertool)
        elif event.key() == Qt.Key_R:
            self.switch_tool(self.marqueetool)
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            if self.tool is self.marqueetool:
                valid, rect = self.roomBuffer.try_copydata(self.marqueetool.entrygridpos, self.marqueetool.endgridpos)
                if valid:
                    self.copytool.indicator.setRect(rect)
                    self.switch_tool(self.copytool)
        elif event.key() == Qt.Key_X and event.modifiers() & Qt.ControlModifier:
            if self.tool is self.marqueetool:
                valid, rect = self.roomBuffer.try_copydata(self.marqueetool.entrygridpos, self.marqueetool.endgridpos)
                if valid:
                    self.movetool.indicator.setRect(rect)
                    self.switch_tool(self.movetool)
        elif event.key() == Qt.Key_Shift:
            self.switch_tool(self.pickertool)

    def receiveKeyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Shift:
            if self.tool is self.pickertool:
                self.switch_tool(self.pentool, True)

    #WARN> 工具回调
    def onSelectionChanged(self):
        '''被选中的对象发生改变时,通知工具'''

    def onEnter(self, event: QEnterEvent):
        '''鼠标进入绘制场景时,通知工具'''
        self.tool.onEnter(event)

    def onLeave(self, event: QEvent):
        '''鼠标离开绘制场景时,通知工具'''
        self.tool.onLeave(event)

    def onClick(self, event:QMouseEvent, isMovingScene:bool):
        '''isMovingScene标记了当前的鼠标移动操作是否是移动场景而非绘制'''
        self.tool.onClick(event, isMovingScene)

    def onMove(self, event: QMouseEvent):
        '''鼠标移动时,通知工具'''
        self.tool.onMove(event)

    def onRelease(self, event: QMouseEvent):
        '''鼠标松开时,通知工具'''
        self.tool.onRelease(event)