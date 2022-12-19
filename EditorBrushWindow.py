# 笔刷窗体

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Euclid.EuclidWindow import *
from Euclid.EuclidWidgets import *
from Editor import _EditorLabel, EditorLabelContainer

class EditorBrushWindow(EuclidWindow):
    '''编辑器的笔刷窗体|临时存储当前所有的笔刷信息'''

    def __init__(self, parent=None):
        super().__init__(parent=parent,title="笔刷盒")
        self.build()

    def build(self):
        '''创建所有的控件'''

        # self.brushlib_list = _EditorBrushLibListBox()
        self.brush_box = EditorLabelContainer()
        self.btn_import = EuclidButton(text="新增瓦片")
        self.btn_savebrushbox = EuclidButton(text="保存笔刷库")
        self.btn_loadbrushbox = EuclidButton(text="加载笔刷库")
        self.setup()

    def setup(self):
        '''对所有空间进行布局'''

        # 主体对象
        self.addh_calc(self.brush_box, (1.0, -110), (1.0, -30))
        # self.addh_calch(self.brushlib_list, 100, (1.0, -30))

        # 按钮
        self.addv(self.btn_import)