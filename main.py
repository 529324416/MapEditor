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
from EditorProjectCreator import *
from EditorData import *


class MapEditorMainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__(None)
        self.setObjectName(EUCLID_MAINWINDOW)
        self.build()
        self.project = None

    def build(self):

        self.brushWindow = EditorBrushWindow(self)
        self.tileWindow = EditorTileWindow(self, labelSize=(50, 64))
        self.roomEditor = EditorMapWindow(self)
        self.createProjectWindow = ProjectCreatorWindow(self)
        self.createProjectWindow.hide()
        self.build_menu()
        self.setup()

    def build_menu(self):
        '''构建菜单'''

        self.menubar = self.menuBar()
        menu_file = self.menubar.addMenu("文件")
        action = menu_file.addAction("创建工程")
        action.triggered.connect(self.create_project)

    def create_project(self):
        '''创建一个新的工程'''

        if self.project != None and not self.project.hasSaved:
            btn = qtutils.question_withcancel(None,"创建工程文件","当前工程未保存,是否保存?")
            if btn == QMessageBox.Ok:
                pass
            elif btn == QMessageBox.Cancel:
                return

        def _(valid:bool, tilesize:tuple):
            '''回调函数'''

            if valid:
                self.project = ProjectData(tilesize)
                self.roomEditor.initproject(self.project)
                self.tileWindow.initproject(self.project)
        self.createProjectWindow.startup(_)

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

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.menubar.resize(self.width(), self.menubar.height())
        return super().resizeEvent(a0)

    def initProject(self):
        '''自动初始化一个新的工程文件'''

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
    sys.exit(app.exec_())