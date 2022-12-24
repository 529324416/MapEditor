# 瓦片库，类似于笔刷库但瓦片库只存储瓦片
# 2022.12.15

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *

from Editor import EditorLabelContainer,EditorListBox
from EditorData import *
import qtutils

class EditorTileWindow(EuclidWindow):
    '''瓦片库窗体'''

    def __init__(self, parent=None, labelSize=(70,86)):
        super().__init__(parent=parent,title="瓦片库")

        self.tileContainer = EditorLabelContainer(labelSize=labelSize)
        self.tileContainer.setObjectName("EditorTileBox")
        self.tileContainer.onLabelChoosed.connect(self.choosetile)

        self.tileliblist = EditorListBox()
        self.tileliblist.elemButtonClicked.connect(self.removelib)
        self.tileliblist.elemClicked.connect(self.renderlib)
        self.tileliblist.elemRenamed.connect(self.renamelib)

        self.btn_makenew = EuclidButton(text="新建库", callback=self.addlib)
        self.btn_import = EuclidButton(text="导入瓦片", callback=self.importtiles)
        self.btn_removetile = EuclidButton(text="删除当前瓦片", callback=self.removetile)
        self.choosedName = None
        self.setup()

        self.project = None

    def setup(self):
        self.addh_calch(self.tileliblist, 100, (1.0, -30))
        self.addh_calc(self.tileContainer,(1.0, -110), (1.0, -30))
        self.addv(self.btn_makenew)
        self.addh(self.btn_import)
        self.addh(self.btn_removetile)

    def initproject(self, project: ProjectData):
        '''根据给定的工程文件来初始化窗体
        设置所有部件的回调函数,以及渲染工程中的瓦片库信息'''

        self.project = project
        self.tileContainer.clear()
        self.tileliblist.clear()
        for lib in self.project.tileManager.libs:
            self.tileliblist.add(lib.name)


    def addlib(self) -> None:
        '''追加一个新的瓦片库'''

        if self.project is None:
            qtutils.information(None,"新建瓦片库","请先创建一个工程文件")
        else:
            lib = self.project.tileManager.createLib()
            self.tileliblist.add(lib.name)
            self.tileContainer.render(lib.render_infos)

    def removelib(self, name:str) -> None:
        '''删除指定的瓦片库
        NOTE> 该函数需要与编辑器通过工程文件进行联动'''

        if self.project is None:return
        index, lib = self.project.tileManager.findLib(name)
        if lib != None and qtutils.question(None,"删除瓦片库",f"是否确认删除库:{lib.name}"):
            self.project.tileManager.removeLib(index)
            self.tileliblist.takeItem(index)
            libidx = self.tileliblist.currentRow()
            if libidx < 0:
                self.choosedName = None
                self.tileContainer.clear()
            else:
                lib = self.project.tileManager.indexLib(libidx)
                self.choosedName = lib.name
                self.tileContainer.render(lib.render_infos)

    def renderlib(self, idx:int):
        '''玩家选中一个瓦片库时执行该函数/该函数认为如果projectData为None时,该函数永远无法被触发'''

        if self.project != None:
            lib = self.project.tileManager.set_current_lib(idx)
            self.tileContainer.render(lib.render_infos)

    def renamelib(self, oldName:str, newName:str, callback:callable):
        '''重命名一个lib\n
        查找要重命名的名字是否被占用了,如果是则取消重命名'''

        if self.project is None:return
        index, libtest = self.project.tileManager.findLib(newName)
        if libtest is None:
            index, lib = self.project.tileManager.findLib(oldName)
            lib.name = newName
            callback(newName)
        else:
            qtutils.information(None,"重命名瓦片库",f"瓦片库名称<{newName}>已经被占用")

    def importtiles(self) -> None:
        '''向当前瓦片库中导入一组瓦片'''

        if self.project is None or self.project.tileManager.currentlib is None:return
        success, failedlist = self.project.tileManager._import_tiles()
        if success:
            self.tileContainer.render(self.project.tileManager.currentlib.render_infos)
            if len(failedlist) > 0:
                qtutils.information(None, "导入瓦片", f"{len(failedlist)}个文件导入失败")

    def removetile(self, index:int) -> None:
        '''从当前瓦片库中删除一张选中的瓦片
        NOTE> 该函数需要与编辑器通过工程文件进行联动'''

        if self.project is None:return
        self.tileContainer.render(self.project.removetile(index))

    def choosetile(self, index:int) -> None:
        '''当前瓦片被选中的时候执行该回调函数
        NOTE> 该函数需要与编辑器通过工程文件进行联动'''

        if self.project is None:return
        self.project.choosetile(index)