# DOC> name: 地图编辑器2.0
# DOC> time: 2022.12.14
# DOC> desc: 重构之前的地图编辑器

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.Euclid import *
from Euclid.EuclidGraphicsView import *
from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *

from utils import *
from qtutils import *
from EditorBrushWindow import *
from EditorTileWindow import *
from EditorMapWindow import *
from EditorRoomWindow import *
from EditorData import *

class MapEditorMainWindow(QWidget):

    def __init__(self) -> None:
        super().__init__(None)
        self.setObjectName(EUCLID_MAINWINDOW)
        self.build()

        self.checkSave = True
        self.initProject()

    def build(self):

        self.brushWindow = EditorBrushWindow(self)
        self.tileWindow = EditorTileWindow(self, labelSize=(50, 64))
        self.roomEditor = EditorMapWindow(self)
        self.setup()

    def setup(self):
        '''设置基本参数'''

        font = QFont("zpix")
        self.setFont(font)
        self.setWindowTitle("地图编辑器2.0")
        style = f"{read('./Qss/euclid.qss')}\n{read('./Qss/editor.qss')}"
        self.setStyleSheet(style)
        EuclidWindow.load_layout(self, "./layout.txt")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.roomEditor.receiveKeyEvent(event)

    def keyReleaseEvent(self, a0) -> None:
        self.roomEditor.receiveKeyReleaseEvent(a0)

    def closeEvent(self, evt: QCloseEvent) -> None:
        '''退出主窗体的时候记录所有窗体的布局信息'''

        if self.project != None and not self.project.hasSaved:
            btn = qtutils.question_withcancel(None,"关闭窗体","是否保存当前的工程文件?")
            if btn == QMessageBox.Cancel:
                evt.ignore()
                return
            elif btn == QMessageBox.Ok:
                print("保存当前的工程文件")
        EuclidWindow.save_layout(self, "./layout.txt")

    def initProject(self):
        '''初始化一个新的工程文件'''

        self.project = ProjectData()
        self.roomEditor.initproject(self.project)
        self.tileWindow.initproject(self.project)

if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    font = QFont("zpix", 9)
    font.setStyleStrategy(QFont.NoAntialias)
    app.setFont(font)
    window = MapEditorMainWindow()
    window.show()
    exit(app.exec_())