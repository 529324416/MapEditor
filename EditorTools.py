# 地图编辑器工具集合


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from Euclid.EuclidGraphicsView import *
from Editor import EditorView, EditorColor
import numpy as np

class ToolType:

    EMPTY = 0           # 空白工具
    PEN = 1
    EARSE = 2
    MARQUEE = 3
    COPY = 4
    MOVE = 5
    ROOMCREATOR = -1
    TILE_PICKER = -2


class ToolHelper:
    '''提供一些简单的辅助API帮助工具快捷的建立功能'''

    def __init__(self, tilesize=(12, 12)):
        self.tilesize = tilesize
        self.tilew, self.tileh = tilesize

    def gridpos(self, pos: QPointF) -> QPoint:
        return QPoint(int(pos.x() // self.tilew), int(pos.y() // self.tileh))

    def scenepos(self, gridpos: QPoint) -> QPointF:
        return QPointF(gridpos.x() * self.tilew, gridpos.y() * self.tileh)

    def qgridsnap(self, pos: QPointF) -> QPointF:
        '''snap to grid position'''

        return QPointF((pos.x() // self.tilew) * self.tilew,(pos.y() // self.tileh) * self.tileh)

    def gridsnap(self, pos: QPointF) -> tuple:
        '''snap to grid position, output tuple'''

        return (pos.x()//self.tilew) * self.tilew, (pos.y()//self.tileh)*self.tileh
    
    def createindicator(self, color: QColor):
        '''创建一个新的QGraphicsRectItem表示鼠标指针指示器'''
        item = QGraphicsRectItem(0, 0, self.tilew, self.tileh)
        item.setPen(color)
        return item

    def createbox(self, color: QColor, size=(40, 30), width=1.0, style=Qt.SolidLine):
        '''创建一个box大小范围单位为瓦片单位'''

        item = QGraphicsRectItem(0, 0, self.tilew * size[0], self.tileh * size[1])
        item.setPen(QPen(color, width, style))
        return item

class ITool(QObject):
    '''Tool接口, 用于定义Tool的基本行为'''

    def __init__(self, view: EditorView, scene: EuclidSceneGrid, name:str, toolType:int, helper:ToolHelper, indicator_color=EditorColor.TEXT_COLOR):
        super().__init__(None)
        self.name = name
        self.view = view
        self.scene = scene
        self.helper = helper
        self.toolType = toolType
        self.indicator = helper.createindicator(indicator_color)
        self.__is_indicator_showing = False
        self.__clicked = False

    @property
    def canDraw(self):
        return self.__clicked

    def show_indicator(self) -> bool:
        '''显示指示器并返回数据是否发生了切换'''

        if self.__is_indicator_showing:return False
        self.__is_indicator_showing = True
        self.scene.addItem(self.indicator)
        return True

    def hide_indicator(self):
        if self.__is_indicator_showing:
            self.__is_indicator_showing = False
            self.scene.removeItem(self.indicator)
            return True
        return False

    def compute_positions(self,event: QMouseEvent):
        '''计算鼠标的原始场景坐标,对齐之后的场景网格坐标以及网格坐标'''

        scenepos = self.view.mapToScene(event.pos())
        pos_snapped = self.helper.gridpos(scenepos)
        scenepos_snapped = self.helper.scenepos(pos_snapped)
        return scenepos_snapped, pos_snapped

    def useTool(self):
        self.view.setSelectable(False)
        self.show_indicator()

    def stopTool(self):
        self.hide_indicator()

    #WARN> Item行为
    def onItemPressed(self, item, event):
        pass

    def onItemMove(self, item, event):
        pass

    def onItemReleased(self, item, event):
        pass

    def onSelectionChanged(self):
        pass

    #WARN>鼠标行为
    def onClick(self, event: QMouseEvent, isNotMoving:bool):
        self.__clicked = isNotMoving and event.button() == Qt.LeftButton

    def onMove(self, event: QMouseEvent):
        pass

    def onRelease(self, event: QMouseEvent):
        self.__clicked = False

    def onEnter(self, event: QEnterEvent):
        self.show_indicator()
        pos = self.view.mapToScene(event.pos())
        self.indicator.setPos(pos)

    def onLeave(self, event: QEvent):
        self.hide_indicator()

    def updatePosition(self, scenepos: QPointF):
        '''直接更新鼠标的位置'''
        self.indicator.setPos(scenepos)

class EmptyTool(ITool):
    '''一个空的工具,试图在房间中绘制一个可以移动的indicator表示鼠标的位置'''

    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "空白工具", ToolType.EMPTY, helper, EditorColor.TEXT_SLIENT)

    def useTool(self):
        '''开始使用该工具'''
        self.view.setSelectable(False)
        self.show_indicator()

    def stopTool(self):
        '''停止使用该工具'''
        self.hide_indicator()

    def onLeave(self, event: QEvent):
        self.hide_indicator()

    def onEnter(self, event: QEnterEvent):
        self.show_indicator()
        pos = self.view.mapToScene(event.pos())
        self.indicator.setPos(self.helper.qgridsnap(pos))

    def onMove(self, event: QMouseEvent):
        pos = self.view.mapToScene(event.pos())
        self.indicator.setPos(self.helper.qgridsnap(pos))

class RoomCreatorTool(ITool):
    '''提供一个工具用于框选房间的范围'''

    onSizeChanged = pyqtSignal(QSize, QPoint, QRectF)

    def __init__(self, view:EditorView, scene:EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "创建房间", ToolType.ROOMCREATOR, helper, EditorColor.SLIENT_COLOR_PURPLE)
        self.border = helper.createbox(EditorColor.EYECATCH_COLOR_CYAN, style=Qt.DashLine)
        self.border.setRect(QRectF())

    def useTool(self):
        self.view.setSelectable(False)
        self.scene.addItem(self.border)
        self.show_indicator()
    
    def stopTool(self):
        self.scene.removeItem(self.border)
        self.border.setRect(QRectF())
        self.hide_indicator()

    def onClick(self, event: QMouseEvent, isNotMoving:bool):
        super().onClick(event, isNotMoving)
        _pos = self.view.mapToScene(event.pos())
        self.startpos = self.helper.qgridsnap(_pos)

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        _pos = self.view.mapToScene(event.pos())
        currentpos = self.helper.qgridsnap(_pos)
        self.indicator.setPos(currentpos)
        if self.canDraw:
            '''调整border的范围'''
            self.reset_border(self.startpos, currentpos)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)

    def reset_border(self, p1: QPoint, p2: QPoint):
        '''重新调整border的大小'''

        rect = QRectF(p1.x(), p1.y(), p2.x() - p1.x(), p2.y() - p1.y())
        self.border.setRect(rect)
        _size = rect.size()
        w = abs(int(_size.width() // self.helper.tilew))
        h = abs(int(_size.height() // self.helper.tileh))

        x = int(rect.x() // self.helper.tilew)
        y = int(rect.y() // self.helper.tileh)

        self.onSizeChanged.emit(QSize(w, h), QPoint(x, y), rect)

class PenTool(ITool):

    drawMoved = pyqtSignal(QPointF, QPoint)

    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "铅笔", ToolType.PEN, helper)
        pixmap = QPixmap("./Res/penicon.png")
        self.defaultpixmap = pixmap.scaled(helper.tilew, helper.tileh)
        self.tileId = 0
        self.indicator = QGraphicsPixmapItem(self.defaultpixmap)
        self.indicator.setZValue(100)

    def __draw(self, event:QMouseEvent):
        '''点击或者拖动时发送绘制请求'''

        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)
        if self.canDraw:
            self.drawMoved.emit(scenepos, gridpos)

    def onClick(self, event: QMouseEvent, isNotMoving: bool):
        super().onClick(event, isNotMoving)
        self.__draw(event)

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        self.__draw(event)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)

class EraserTool(ITool):

    drawMoved = pyqtSignal(QPointF, QPoint)

    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "橡皮", ToolType.EARSE, helper)
        self.indicator.setZValue(101)

    def __draw(self, event:QMouseEvent):
        '''点击或者拖动时发送绘制请求'''

        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)
        if self.canDraw:
            self.drawMoved.emit(scenepos, gridpos)

    def onClick(self, event: QMouseEvent, isNotMoving: bool):
        super().onClick(event, isNotMoving)
        self.__draw(event)

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        self.__draw(event)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)

class MarqueeTool(ITool):
    '''选框工具,提供一个工具用于切换选框'''

    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "选框", ToolType.MARQUEE, helper, EditorColor.EYECATCH_COLOR_RED)
        self.indicator.setZValue(102)
        self.border = QGraphicsRectItem()
        self.border.setZValue(102)
        self.border.setPen(QPen(EditorColor.EYECATCH_COLOR_RED, 1.0, Qt.DashLine))
        self.border.setRect(0, 0, 0, 0)
        self.entrypos = QPointF(0, 0)

    def useTool(self):
        '''开始使用该工具'''

        self.border.setRect(0, 0, 0, 0)
        self.view.setSelectable(False)
        self.scene.addItem(self.border)
        self.show_indicator()

    def stopTool(self):
        '''停止使用该工具'''
        self.hide_indicator()
        self.scene.removeItem(self.border)

    def onEnter(self, event: QEnterEvent):
        self.show_indicator()
        pos = self.view.mapToScene(event.pos())
        self.indicator.setPos(pos)

    def __draw(self, event:QMouseEvent):
        '''点击或者拖动时发送绘制请求'''

        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)
        if self.canDraw:
            self.border.setRect(QRectF(self.entrypos, scenepos))
            self.endgridpos = gridpos

    def onClick(self, event: QMouseEvent, isNotMoving: bool):
        super().onClick(event, isNotMoving)
        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)
        self.entrypos = scenepos
        self.entrygridpos = gridpos

        if self.canDraw:
            self.border.setRect(QRectF(self.entrypos, scenepos))
            self.endgridpos = gridpos

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        self.__draw(event)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)

class CopyTool(ITool):
    '''复制一组数据'''

    clicked = pyqtSignal(QPoint)
    rightClicked = pyqtSignal()
    
    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "复制工具", ToolType.COPY, helper, EditorColor.EYECATCH_COLOR_RED)
        self.indicator.setZValue(103)

    def onClick(self, event: QMouseEvent, isNotMoving:bool):
        super().onClick(event, isNotMoving)
        if event.button() == Qt.LeftButton and isNotMoving:
            scenepos, gridpos = self.compute_positions(event)
            self.indicator.setPos(scenepos)
            self.clicked.emit(gridpos)
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit()

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)

class MoveTool(ITool):
    
    clicked = pyqtSignal(QPoint)
    rightClicked = pyqtSignal()
    
    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "移动工具", ToolType.MOVE, helper, EditorColor.EYECATCH_COLOR_ORANGE)
        self.indicator.setZValue(103)

    def onClick(self, event: QMouseEvent, isNotMoving:bool):
        super().onClick(event, isNotMoving)
        if event.button() == Qt.LeftButton and isNotMoving:
            scenepos, gridpos = self.compute_positions(event)
            self.indicator.setPos(scenepos)
            self.clicked.emit(gridpos)
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit()

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)


class TilePickerTool(ITool):

    clicked = pyqtSignal(QPointF, QPoint)
    
    def __init__(self, view: EditorView, scene: EuclidSceneGrid, helper: ToolHelper):
        super().__init__(view, scene, "滴灌工具", ToolType.TILE_PICKER, helper, EditorColor.EYECATCH_COLOR_PURPLE)
        self.indicator.setZValue(104)

    def onClick(self, event: QMouseEvent, isNotMoving: bool):
        super().onClick(event, isNotMoving)
        scenepos, snapped_pos = self.compute_positions(event)
        self.indicator.setPos(scenepos)
        if self.canDraw:
            self.clicked.emit(scenepos, snapped_pos)

    def onRelease(self, event: QMouseEvent):
        super().onRelease(event)

    def onMove(self, event: QMouseEvent):
        super().onMove(event)
        scenepos,gridpos = self.compute_positions(event)
        self.indicator.setPos(scenepos)