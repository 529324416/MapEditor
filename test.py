import sys
from PyQt5.QtWidgets import QApplication
from euclid import *

class Window(QLabel):

    def __init__(self):
        super().__init__(None)
        self.setObjectName("EuclidBaseWindow")
        self.resize(int(1308*0.8), int(1120*0.8))
        self.build()
        self.show()

    def build(self):
        
        with open("./style.qss", encoding='utf-8') as f:
            self.setStyleSheet(f.read())
        self.window = EuclidWindow(parent=self)
        self.window.resize(200, 250)



        self.window2 = EuclidWindow(parent=self, has_title=False)
        self.window2.resize(200, 250)
        btn = EuclidButton()
        btn.setFixedSize(100, 30)
        btn.clicked.connect(lambda:self.window2.enable_title())
        btn.setParent(self.window2)


        restore_window_status("./test.json")

    def closeEvent(self, a0):
        store_window_status(EuclidWindow.window_list, "./test.json")


app = QApplication(sys.argv)
window = Window()
exit(app.exec_())