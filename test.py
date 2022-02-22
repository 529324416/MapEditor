import sys
from PyQt5.QtWidgets import QApplication
from euclid import *

class Window(QWidget):

    def __init__(self):
        super().__init__(None)
        self.setObjectName("EuclidBaseWindow")
        self.resize(1000, 600)
        self.build()
        self.show()

    def build(self):
        
        with open("./style.qss", encoding='utf-8') as f:
            self.setStyleSheet(f.read())
        self.window = EuclidWindow(parent=self)
        self.window.setObjectName("EuclidWindow")
        self.window.resize(200, 250)


app = QApplication(sys.argv)
window = Window()
exit(app.exec_())