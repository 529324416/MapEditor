

from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *
from Euclid.EuclidGraphicsView import EuclidView
import queue

class EditorColor:

    BACKGROUND_COLOR_LEVEL0 = QColor("#1A1C2C")
    BACKGROUND_COLOR_LEVEL0_095ALPHA = QColor("#1A1C2CF2")
    BACKGROUND_COLOR_LEVEL1 = QColor("#282941")
    BACKGROUND_COLOR_LEVEL2 = QColor("#3c4557")

    TEXT_COLOR = QColor("#FFFDE3")
    TEXT_SLIENT = QColor("#b0ac80")
    
    EYECATCH_COLOR_CYAN = QColor("#00FFA5")
    EYECATCH_COLOR_ORANGE = QColor("#ffbe00")
    EYECATCH_COLOR_RED = QColor("#ff003c")
    EYECATCH_COLOR_PURPLE = QColor("#5000ff")

    SLIENT_COLOR_PURPLE = QColor("#5655a6")
    SLIENT_COLOR_GREEN = QColor("#78a655")

class EditorLabelContainer(EuclidScrollArea):
    '''EditorLabel的容器盒子'''

    onLabelChoosed = pyqtSignal(int)
    '''当第index个label被选中的时候,该信号触发'''

    def __init__(self, parent=None, labelSize=(50, 64)):
        super().__init__(parent=parent)

        self.labelList = list()
        self.labelSize = labelSize
        self.recycleQueue = queue.Queue()
        self.gridLayout = QGridLayout(self.container)
        self.gridLayout.setAlignment(Qt.AlignLeft| Qt.AlignTop)
        self.choosedLabel = None
        self.choosedIndex = -1
        self.row = 1

    def _onLabelChoosed(self, index:int):
        '''回调函数(当Label被选中)'''

        if self.choosedIndex != index:
            self.choosedIndex = index
            if self.choosedLabel != None:
                restyle(self.choosedLabel, "EditorLabel")
            self.choosedLabel = self.labelList[index]
            restyle(self.choosedLabel, "EditorLabelChoosed")
            self.onLabelChoosed.emit(index)

    def clear(self):
        '''清空所有的渲染'''

        self.checkCount(0)
        self.choosedLabel = None
        self.choosedIndex = -1

    def render(self, brushes:list):
        '''渲染一组笔刷信息(注意,只有笔刷信息,而不是具体的数据概念)'''

        # 清空之前的选中对象
        if self.choosedLabel != None:
            restyle(self.choosedLabel, "EditorLabel")
            self.choosedLabel = None
        self.choosedIndex = -1;

        _count = len(brushes)
        self.checkCount(_count)
        self.row = max(1, self.container.width() // self.labelSize[0])

        for idx, info in enumerate(brushes):
            label = self.labelList[idx]
            self.gridLayout.addWidget(label, idx // self.row, idx % self.row, 1, 1)
            label.render(info[0], info[1])
            label.index = idx
        self._updateLayout(_count)

    def generate(self):
        '''创建一个新的Label'''

        if self.recycleQueue.empty():
            return _EditorLabel(self._onLabelChoosed, self.labelSize)
        label = self.recycleQueue.get()
        label.setFixedSize(*self.labelSize)
        label.show()
        return label

    def checkCount(self, count:int) -> bool:
        '''确保当前的Label数量为count'''

        _count = len(self.labelList)
        if _count == count:return False
        if _count > count:
            for i in range(_count - count):
                label = self.labelList.pop()
                label.hide()
                self.gridLayout.removeWidget(label)
                self.recycleQueue.put(label)
            return True
        else:
            for i in range(count - _count):                
                self.labelList.append(self.generate())
            return True

    def updateLayoutSize(self):
        '''调整当前网格布局的排布 '''

        count = len(self.labelList)
        rowLength = max(1, self.container.width() // self.labelSize[0])
        if rowLength != self.row and count >= rowLength:
            # 横轴长度发生变化, 需要更新所有的渲染器位置

            self.row = rowLength
            self._updateLayout(count)

    def _updateLayout(self, count):
        '''更新容器布局'''

        row = self.row
        for idx, label in enumerate(self.labelList):
            self.gridLayout.addWidget(label, idx // row, idx % row, 1, 1)
        h = count // row if count % row == 0 else (count // row) + 1
        self.container.setMinimumHeight(h * self.labelSize[1])

    def resizeEvent(self, evt: QResizeEvent):
        _size = evt.size()
        self.container.resize(_size.width(), max(_size.height() - 10, self.container.minimumHeight()))
        self.updateLayoutSize()
        super().resizeEvent(evt)

class _EditorLabel(QLabel):
    '''显示一张图片+标题'''

    def __init__(self, clickCallback, size=(50,64), parent=None):
        super().__init__(parent=parent)
        self.setObjectName("EditorLabel")
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.clickCallback = clickCallback

        self.pictureBox = QLabel(self)
        self.pictureBox.setObjectName("EditorLabel_picturebox")
        self.pictureBox.setAlignment(Qt.AlignCenter)
        self.pictureBox.setFixedSize(size[0] - 2, size[0] - 2)
        self.pictureBox.move(1, 1)

        self.title = QLabel(self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFixedSize(size[0], size[1] - size[0])
        self.title.move(0, size[0])

        self.index = 0

    def mousePressEvent(self, ev) -> None:
        self.clickCallback(self.index)
        return super().mousePressEvent(ev)

    def render(self, text:str, picture:QPixmap):
        '''渲染笔刷信息'''

        self.title.setText(text)
        if picture.height() > picture.width():
            _pixmap = picture.scaledToHeight(self.height())
        else:
            _pixmap = picture.scaledToWidth(self.width())
        self.pictureBox.setPixmap(_pixmap)

    # def mousePressEvent(self, ev: QMouseEvent):
    #     if ev.button() == Qt.RightButton:
    #         self.entryPoint = ev.pos()
    #         self.pressed = True

    # def mouseMoveEvent(self, evt: QMouseEvent) -> None:
    #     if self.pressed:
    #         if (evt.pos() - self.entryPoint).manhattanLength() >= QApplication.startDragDistance():
    #             e = QDrag(self)
    #             mimeData = QMimeData()
    #             mimeData.setParent(self)
    #             mimeData.setProperty("brush", self.brush)
    #             e.setMimeData(mimeData)
    #             e.exec_()
    #     return super().mouseMoveEvent(evt)

    # def mouseReleaseEvent(self, evt) -> None:
    #     if evt.button() == Qt.RightButton:
    #         self.pressed = False
    #     elif evt.button() == Qt.LeftButton:
    #         restyle(self.pictureBox, "IndicatorChoozed")
    #         self.callback(self)


class EditorListItem(QWidget):
    '''一个支持编辑的Item,自身携带一个按钮'''

    def __init__(self, name, textChanged, onButtonClicked, onChoosed, onMoveBrush, padding=5):
        super().__init__(parent=None)
        self.name = name
        self.onChoosed = onChoosed
        self.onTextChanged = textChanged
        self.onMoveBrush = onMoveBrush
        self.isEditing = False
        
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(padding, 0, 0, 0)

        # DOC> 创建所有的空间
        self.button = EuclidButton(text="")
        self.button.set_callback(lambda:onButtonClicked(self.name))
        self.button.setFixedSize(12, 12)
        self.label = QLabel()
        self.editor = EuclidLineEditor(self.quitEdit)
        self.editor.returnPressed.connect(self.editDone)
        self.editor.hide()

        # DOC> 排布
        self._layout.addWidget(self.button)
        self._layout.addWidget(self.label)
        self._layout.addWidget(self.editor)

    def dragEnterEvent(self, evt) -> None:
        evt.acceptProposedAction()
        restyle(self.label, "dragEnter")
        return super().dragEnterEvent(evt)

    def dropEvent(self, e: QDropEvent) -> None:
        self.onMoveBrush(self.name, e.mimeData().property("brush"))
        restyle(self.label, "normal")
        return super().dropEvent(e)

    def dragLeaveEvent(self, evt) -> None:
        restyle(self.label, "normal")
        return super().dragLeaveEvent(evt)

    def mousePressEvent(self, event) -> None:
        self.onChoosed(self.name)
        super().mousePressEvent(event)

    def editDone(self):

        def _confirm(name):
            self.label.setText(name)
            self.name = name

        text = self.editor.text().strip()
        if len(text) > 0 and self.name != text:
            self.onTextChanged(self.name, text, _confirm)
        self.quitEdit()

    def quitEdit(self):
        if self.isEditing:
            self.isEditing = False
            self.editor.hide()
            self.label.show()

    def enterEdit(self):
        self.isEditing = True
        self.label.hide()
        self.editor.show()
        self.editor.setText(self.label.text())
        self.editor.setFocus(True)

    def mouseDoubleClickEvent(self, event) -> None:
        self.enterEdit()


class EditorListBox(EuclidListView):
    '''一个简单的列表,渲染一组文本数据并支持修改文本、新增和删除等基本操作'''

    elemClicked = pyqtSignal(str)
    elemRenamed = pyqtSignal(str, str, object)
    elemDropped = pyqtSignal()
    elemButtonClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("EditorListBox")

    def _onChoosed(self, name):
        self.elemClicked.emit(name)

    def _onRenamed(self, oldName, newName, callback):
        self.elemRenamed.emit(oldName, newName, callback)

    def _onDeleted(self, name):
        self.elemButtonClicked.emit(name)

    def _onReceived(self, name, content):
        self.elemDropped.emit(name, content)

    def setItems(self, texts:list):
        '''删除所有的已经存在的元素并重新设置一组数据信息'''

        self.clear()
        for text in texts:
            self.add(text)

    def add(self, name):
        '''添加一个新的元素'''

        item = EditorListItem(name, self._onRenamed, self._onDeleted, self._onChoosed, self._onReceived)
        item.label.setText(name)
        item.resize(80, 30)

        holder = QListWidgetItem()
        self.addItem(holder)
        self.setItemWidget(holder, item)
        self.setCurrentItem(holder)


class EditorView(EuclidView):

    onClicked = pyqtSignal(QMouseEvent, bool)
    onMove = pyqtSignal(QMouseEvent)
    onEnter = pyqtSignal(QEnterEvent)
    onLeave = pyqtSignal(QEvent)
    onRelease = pyqtSignal(QMouseEvent)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def setSelectable(self, value):
        self.setBaseRubberBand(QGraphicsView.RubberBandDrag if value else QGraphicsView.NoDrag)

    def mousePressEvent(self, event):
        self.onClicked.emit(event, super().mousePressEvent(event))
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        self.onRelease.emit(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        self.onMove.emit(event)

    def enterEvent(self, event: QEnterEvent):
        self.onEnter.emit(event)

    def leaveEvent(self, event: QMouseEvent):
        self.onLeave.emit(event)