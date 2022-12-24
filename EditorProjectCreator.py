'''
    when you try to create a new window, you would input some informations 
    into this window, and create project with it, it's a modal window like a dialog
'''


from PyQt5.QtCore import *
from Euclid import *
import qtutils

class ProjectCreatorWindow(EuclidWindow):

    def __init__(self, parent=None, padding=5, sizegripSize=12, titleHeight=20, title="创建新工程文件", minsize=(100, 100), hasButtons=True, **kwargs):
        super().__init__(parent, padding, sizegripSize, titleHeight, title, minsize, hasButtons, **kwargs)
        self.callback = None
        self.build()

    def build(self):
        self.tilesizeLabel = QLabel()
        self.tilesizeLabel.setText("设置瓦片大小")
        self.lineInput_tilew = EuclidLineEditor(None)
        self.lineInput_tileh = EuclidLineEditor(None)
        self.btn_confirm = EuclidButton(text="确认", callback=self.confirm)
        self.btn_cancel = EuclidButton(text="取消", callback=self.cancel)
        self.setup()

    def setup(self):
        self.addh(self.tilesizeLabel, 1.0, 20)
        self.addv(self.lineInput_tilew, 1.0, 20)
        self.addv(self.lineInput_tileh, 1.0, 20)
        self.addv(self.btn_confirm, 1.0)
        self.addv(self.btn_cancel, 1.0)

    def startup(self, callback:callable) -> tuple:
        '''启动并进行数据收集'''

        self.callback = callback
        self.setWindowModality(Qt.ApplicationModal)
        self.show()

    def confirm(self):
        '''确认创建'''

        try:
            w = int(self.lineInput_tilew.text())
            h = int(self.lineInput_tileh.text())
            self.callback(True, (w, h))
            self.setWindowModality(Qt.NonModal)
            self.hide()
        except Exception as e:
            qtutils.information(None, "创建工程文件", f"无效的参数:{str(e)}")

    def cancel(self):
        '''取消创建'''
        self.callback(False, None)
        self.hide()