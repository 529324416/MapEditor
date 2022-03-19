from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from euclid import *
import sys

ITEMPROXY_STYLE = '''
    QPushButton#red{
        border-radius:6px;
        background-color:#c74446;
    }
    QPushButton#red:pressed{
        background-color:#9f3847;
    }
    QPushButton#red:hover{
        background-color:#e84f51;
    }
    QPushButton#normal{
        border-radius:6px;
        background-color:#4da6ff;
    }
    QPushButton#normal:pressed{
        background-color:#327ac3;
    }
    QPushButton#normal:hover{
        background-color:#85c2ff;
    }
    QPushButton#disable{
        border-radius:6px;
        background-color:#a9a9a9;
    }
    QPushButton#disable:pressed{
        background-color:#898989;
    }
    QPushButton#disable:hover{
        background-color:#cdcdcd;
    }
    QLabel#normal{
        color:#ffffeb;
    }
    QLabel#dragEnter{
        color:#ff6b97;
    }
'''


class SimpleEditor(QLineEdit):

    def __init__(self, focusOutCallback, parent=None):
        super().__init__(parent=parent)
        self.focb = focusOutCallback

    def focusOutEvent(self, event) -> None:
        self.focb()
        return super().focusOutEvent(event)


class ItemProxy(QWidget):

    def __init__(self, Id, textChanged, deleteCallback, visibleCallback, chooseCallback, padding=5):
        super().__init__(parent=None)
        self.Id = Id

        self.setFocusPolicy(Qt.StrongFocus)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(padding, 0, 0, 0)

        self.button = QPushButton()
        self.button.setObjectName("red")
        self.button.clicked.connect(lambda :deleteCallback(self.Id))
        self.button.setFixedSize(12, 12)

        self.button2 = QPushButton()
        self.button2.setObjectName("normal")
        self.button2.clicked.connect(self.changeVisible)
        self.button2.setFixedSize(12, 12)
        self._layout.addWidget(self.button)
        self._layout.addWidget(self.button2)

        self.setStyleSheet(ITEMPROXY_STYLE)


        self.label = QLabel()
        self.label.setObjectName(EuclidNames.LABEL)
        self._layout.addWidget(self.label)
        
        self.editor = SimpleEditor(self.quitEdit)
        self.editor.returnPressed.connect(self.editDone)
        self.isEditing = False
        self._layout.addWidget(self.editor)
        self.editor.hide()

        self.visibleCallback = visibleCallback
        self.textCallback = textChanged
        self.chooseCallback = chooseCallback

    def changeVisible(self):
        if self.visibleCallback(self.Id):
            restyle(self.button2, "normal")
        else:
            restyle(self.button2, "disable")

    def _setVisible(self, value):
        restyle(self.button2, "normal" if value else "disable")

    def editDone(self):
        text = self.editor.text().strip()
        if len(text) > 0:
            if self.Id != text:
                if self.textCallback(self.Id, text):
                    self.label.setText(text)
                    self.Id = text
        self.quitEdit()

    def mousePressEvent(self, event) -> None:
        self.chooseCallback(self.Id)
        return super().mousePressEvent(event)
 
    def enterEdit(self):
        self.isEditing = True
        self.label.hide()
        self.editor.show()
        self.editor.setText(self.label.text())
        self.editor.setFocus(True)

    def quitEdit(self):
        if self.isEditing:
            self.isEditing = False
            self.editor.hide()
            self.label.show()

    def mouseDoubleClickEvent(self, event) -> None:
        self.enterEdit()


class SimpleListWidget(QListWidget):

    def __init__(self, dataCallback, deleteCallback, visibleCallback, chooseCallback, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("EditorBrushContainerList")
        self.dataCallback = dataCallback
        self.deleteCallback = deleteCallback
        self.chooseCallback = chooseCallback
        self.visibleCallback = visibleCallback
        self.setCurrentItem(None)

    def add(self, Id):
        proxy = ItemProxy(Id, self.dataCallback, self.deleteCallback, self.visibleCallback, self.chooseCallback)
        proxy.label.setText(Id)
        proxy.resize(300, 40)
        item = QListWidgetItem()
        self.addItem(item)
        self.setItemWidget(item, proxy)
        return proxy


class ItemProxySingleBtn(QWidget):
    '''类似于ItemProxy, 但仅有一个删除按钮'''

    def __init__(self, Id, textChanged, onDeleted, onChoosed, onMoveBrush, padding=5):
        super().__init__(parent=None)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet(ITEMPROXY_STYLE)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(padding, 0, 0, 0)

        self.button = QPushButton()
        self.button.setObjectName("red")
        self.button.clicked.connect(lambda:onDeleted(Id))
        self.button.setFixedSize(12, 12)
        self._layout.addWidget(self.button)

        self.label = QLabel()
        self.label.setObjectName("normal")
        self.label.setObjectName(EuclidNames.LABEL)
        self._layout.addWidget(self.label)

        self.editor = SimpleEditor(self.quitEdit)
        self.editor.returnPressed.connect(self.editDone)
        self._layout.addWidget(self.editor)
        self.editor.hide()

        self.Id = Id
        self.onChoosed = onChoosed
        self.onTextChanged = textChanged
        self.onMoveBrush = onMoveBrush
        self.isEditing = False

        self.setAcceptDrops(True)

    def dragEnterEvent(self, evt) -> None:
        evt.acceptProposedAction()
        restyle(self.label, "dragEnter")
        return super().dragEnterEvent(evt)

    def dropEvent(self, e: QDropEvent) -> None:
        self.onMoveBrush(self.Id, e.mimeData().property("brush"))
        restyle(self.label, "normal")
        return super().dropEvent(e)

    def dragLeaveEvent(self, evt) -> None:
        restyle(self.label, "normal")
        return super().dragLeaveEvent(evt)

    def mousePressEvent(self, event) -> None:
        self.onChoosed(self.Id)
        super().mousePressEvent(event)

    def editDone(self):
        text = self.editor.text().strip()
        if len(text) > 0:
            if self.Id != text:
                if self.onTextChanged(self.Id, text):
                    self.label.setText(text)
                    self.Id = text
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

class SimpleListWidgetSingleBtn(QListWidget):

    def __init__(self, onTextChanged, onDeleted, onChoosed, onMoveBrush, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("EditorBrushContainerList")
        self.onTextChanged = onTextChanged
        self.onDeleted = onDeleted
        self.onChoosed = onChoosed
        self.onMoveBrush = onMoveBrush
        self.setCurrentItem(None)
        
    #     self.setAcceptDrops(True)

    # def dragEnterEvent(self, e) -> None:
    #     e.acceptProposedAction()
    #     # return super().dragEnterEvent(e)

    def add(self, Id):
        proxy = ItemProxySingleBtn(Id, self.onTextChanged, self.onDeleted, self.onChoosed, self.onMoveBrush)
        proxy.label.setText(Id)
        proxy.resize(300, 40)
        item = QListWidgetItem()
        self.addItem(item)
        self.setItemWidget(item, proxy)
        return proxy

class InputBox(QWidget):

    def __init__(self, prompt="输入框", parent=None):
        super().__init__(parent=parent)
        self._layout = QHBoxLayout(self)
        self.label = QLabel(text=prompt)
        self.editor = QLineEdit()
        self.editor.setStyleSheet("color:black;")
        self._layout.addWidget(self.label)
        self._layout.addWidget(self.editor)

    def setEditText(self, text):
        self.editor.setText(text)

    def editText(self):
        return self.editor.text()


def makeButtons(buttonList:list):

    layout = QHBoxLayout()
    for args in buttonList:
        button = QPushButton(args[0])
        button.clicked.connect(args[1])
        layout.addWidget(button)
    return layout


class RoomCreatorHelper(EuclidWindow):
    '''该窗体用以辅助创建一个新的房间'''

    def __init__(self, confirmCB, cancelCB, parent=None):
        super().__init__(parent=parent, has_title=False, minsize=(100, 50))
        self.resize(260, 50)
        self.setup(confirmCB, cancelCB)
        EuclidWindow.setOnTop(self)

    def setup(self, confirmCB, cancelCB):

        self.indicator = EuclidMiniIndicator()
        self.indicator.invalid()
        self.add(self.indicator)
        self.statusLabel = EuclidLabel(size=(60, 14), text="创建房间")
        self.addh(self.statusLabel)
        self.addh(EuclidLabel(size=(5, 14), text="|"))
        self.info = EuclidLabel(size=(250, 14), text="框选房间范围..")
        self.addh(self.info)

        self.confirmBtn = EuclidButton(title="确认", callback=confirmCB)
        self.add(self.confirmBtn)
        self.confirmBtn.invalid()
        self.addh(EuclidButton(title="取消", callback=cancelCB))
        self.hideSizeGrip()

    def setTitle(self, title):
        self.statusLabel.setText(title)

    def clear(self):
        '''重新启动之前清空现在的数据'''

        self.indicator.invalid()
        self.info.normal("请框选房间范围")
        self.confirmBtn.invalid()
        self.cpos = (0, 0)
        self.csize = (1, 1)

    def hideEvent(self, ev) -> None:
        self.clear()
        return super().hideEvent(ev)

    def collisionWarning(self):
        '''警告用户所框选的房间不符合条件'''

        self.indicator.invalid()
        self.confirmBtn.invalid()
        self.info.warning("和其他房间冲突")

    def sizeWarning(self):
        '''警告用户所框选的房间太小'''

        self.indicator.invalid()
        self.confirmBtn.invalid()
        self.info.warning("空间不足以放置原房间数据")
        
    def receiveData(self, p, size):
        '''接受MapEditor的数据'''

        if size[0] < 6 or size[1] < 6:
            self.confirmBtn.invalid()
            self.info.error("#房间尺寸太小(至少为(6x6))")
            self.indicator.invalid()
        else:
            # print(p)
            self.cpos = p
            self.csize = size
            self.indicator.run()
            self.confirmBtn.resume()
            self.info.normal(f"pos:{self.cpos}, size:{self.csize}")

    def receiveAdjustData(self, p1:tuple, size:tuple, lb:tuple, rt:tuple):
        '''接受MapEditor重新调整房间大小的数据信息'''

        if size[0] < 6 or size[1] < 6:
            self.confirmBtn.invalid()
            self.info.error("#调整后的房间尺寸太小(至少为6x6)")
            self.indicator.invalid()
        else:
            self.cpos = p1
            self.csize = size
            self.lb = lb
            self.rt = rt
            self.indicator.run()
            self.confirmBtn.resume()
            self.info.normal(f"pos:{self.cpos}, size:{self.csize}")

    def adjustArgs(self):
        return self.cpos, self.csize, self.lb, self.rt


class RoomCreator(QDialog):

    def __init__(self, callback, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.content = QLabel(self)
        # self.content.setObjectName("CreatorContainer")
        # self.setStyleSheet('''#CreatorContainer{
        #     background-color:rgba(39, 39, 54, 200);
        #     border-radius:2px;
        #     border:1px solid grey;
        # }
        # QLabel{color:#ffffeb;}
        # QPushButton{border-radius:2px;border:none;background-color:#5a8090;color:#ffffeb;min-height:20px;}
        # QPushButton:hover{background-color:#54adb0;}
        # QPushButton:pressed{background-color:#465374;}
        # ''')
        self.content.setGeometry(0, 0, 300, 200)

        self._layout = QVBoxLayout(self.content)
        self._layout.setAlignment(Qt.AlignTop)
        self.widthInput = InputBox("副本宽度")
        self.widthInput.setEditText("128")
        self.heightInput = InputBox("副本高度")
        self.heightInput.setEditText("128")
        self._layout.addWidget(self.widthInput)
        self._layout.addWidget(self.heightInput)

        self.subLayout = QHBoxLayout()
        self.buttonConfirm = QPushButton("确认")
        self.buttonCancel = QPushButton("取消")
        self.buttonConfirm.clicked.connect(self.onConfirm)
        self.buttonCancel.clicked.connect(self.onCancel)

        self.subLayout.addWidget(self.buttonConfirm)
        self.subLayout.addWidget(self.buttonCancel)
        self._layout.addLayout(self.subLayout)

        self.result = False
        self.size = None
        self.callback = callback

    def onConfirm(self):
        '''确认创建副本'''

        try:
            width = int(self.widthInput.editText())
            height = int(self.heightInput.editText())
            self.accept()
            self.callback((width, height))
        except Exception as e:
            print(e)
            QMessageBox.information(None, "错误报告", "无效的参数", QMessageBox.Ok)        

    def onCancel(self):
        '''取消创建副本'''

        self.reject()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.content.resize(self.width(), self.height())

class ProjectCreator(QDialog):

    def __init__(self, callback, parent=None, title="创建新工程", content="输入工程名"):
        super().__init__(parent)
        self.callback = callback
        self.setWindowTitle(title)
        self._layout = QVBoxLayout(self)
        self.nameInput = InputBox(content)
        self._layout.addWidget(self.nameInput)
        buttons = makeButtons([
            ("确认", self.confirm),
            ("取消", self.cancel)
        ])
        self._layout.addLayout(buttons)

    def confirm(self):
        text = self.nameInput.editText().strip()
        if len(text) > 0:
            self.callback(text)
            self.accept()
        else:
            QMessageBox.information(None, "错误报告", "输入的名称无效", QMessageBox.Ok)

    def cancel(self):
        self.reject()








def questionDelete(title):
    '''询问是否删除?'''

    return QMessageBox.question(None, title, "是否确认删除?", QMessageBox.Ok|QMessageBox.Cancel)
    
def warning(title, content):
    QMessageBox.information(None, title, content, QMessageBox.Ok)


def constraint(tiles: list) -> tuple:
    '''给定一组瓦片, 计算容纳改组瓦片所需要空间起始点'''

    if len(tiles) == 0:
        return (0, 0), (0, 0)
    else:
        _tile = tiles[0]
        lb, rt = [_tile.cx, _tile.cy], [_tile.cx + _tile.cwidth, _tile.cy + _tile.cheight]
        for tile in tiles[1:]:
            lb[0] = min(lb[0], tile.cx)
            lb[1] = min(lb[1], tile.cy)
            rt[0] = max(rt[0], tile.cx + tile.size[0])
            rt[1] = max(rt[1], tile.cy + tile.size[1])
        return lb, rt

class Window(QWidget):

    def __init__(self):
        super().__init__(parent=None)
        self.inputbox = InputBox(parent=self)

        self.resize(1000, 600)
        self.show()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = Window()
    exit(app.exec_())