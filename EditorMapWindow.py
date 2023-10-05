# 绘制用的主窗体

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *
from Euclid.EuclidGraphicsView import *
from Editor import *
from EditorData import ProjectData, Tile
from EditorRoomBuffer import RoomDrawingBuffer
from EditorTools import *

import qtutils
import utils

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
        self.btn_exportdata = EuclidButton(text="导出地图数据", callback=self.export_current_room)
        self.btn_exportimage = EuclidButton(text="导出地图图片", callback=self.export_room_image)
        
        #DOC> 建立布局
        self.addh(self.message, 150, 20)
        self.addh(self.btn_pen, 50, 20)
        self.addh(self.btn_eraser, 50, 20)
        self.addh(self.btn_marquee, 50, 20)
        self.addv_calch(self.layerList, 80, (1.0, -60))
        self.addh_calc(self.view, (1.0, -90), (1.0, -60))
        self.addv(self.btn_createroom)
        self.addh(self.btn_exportimage)
        self.addh(self.btn_exportdata)

        #DOC> 其他初始化设置
        self.disable()
        self.tool = FakeTool()
        self.last_tool = FakeTool()
        self.pentool = None
        self.erasertool = None
        self.copytool = None
        self.roomTool = None
        self.emptyTool = None
        self.movetool = None
        self.marqueetool = None
        self.project = None
        self.roomBuffer = None

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
            self.last_tool = self.tool
            self.usetool(tool)
            tool.updatePosition(self.last_tool.indicator.pos())
            return True
        return False

    def enable(self):
        '''启用所有的部件'''
        self.message.setText("编辑器启用")
        self.view.setEnabled(True)
        self.btn_createroom.enable()
        self.btn_exportimage.enable()
        self.btn_exportdata.enable()
        self.usetool(self.emptyTool)

    def disable(self):
        '''禁用所有部件'''
        self.message.setText("编辑器已禁用")
        self.view.setEnabled(False)
        self.btn_createroom.disable()
        self.btn_exportimage.disable()
        self.btn_exportdata.disable()

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

    def export_room_image(self):
        '''将当前房间作为一张图导出'''

        if self.roomBuffer is None:
            qtutils.information(None, "导出地图图片", "当前没有建立房间")
            return
        filepath = qtutils.savefile("导出地图数据",filter="png文件(*.png)")
        if filepath is None:
            return
        tilew, tileh = self.roomBuffer.tilesize
        buffer = QPixmap(self.roomBuffer.room.width * tilew, self.roomBuffer.room.height * tileh)
        buffer.fill(QColor("#00000000"))
        painter = QPainter()
        painter.begin(buffer)
        for layer, tilemap in self.roomBuffer.room.layers.items():
            for pos, tile in tilemap.tilemap.items():
                if tile is None:
                    continue
                painter.drawPixmap(pos[0] * tilew, buffer.height() - pos[1] * tileh, tilew, tileh, tile.pixmap())
        painter.end()
        buffer.save(filepath)

    def export_current_room(self):
        '''打印选框中的数据'''

        if self.roomBuffer is None:
            qtutils.information(None, "导出地图数据", "当前没有建立房间")
        else:
            filepath = qtutils.savefile("导出地图数据")
            if filepath != None:
                obj = self.project.json
                obj.setdefault("room", self.roomBuffer.room.json)
                utils.save_json(obj, filepath)

    def choose_tile(self, tileId:int, pixmap:QPixmap):
        '''分离出来主要是因为选取瓦片的方式不止从瓦片库选择一种，还可以用滴灌来选取'''

        self.pentool.tileId = tileId
        self.pentool.indicator.setPixmap(pixmap)
        self.roomBuffer.current_tile = (tileId, pixmap)

    @property
    def lastTool(self):
        return self.last_tool if self.last_tool != None else self.emptyTool

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