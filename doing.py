from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class Window(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.resize(1000, 600)
        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignLeft|Qt.AlignTop)

        button = QPushButton("1")
        button.setFixedSize(80, 20)
        self.layout.addWidget(button)

        button = QPushButton("2")
        button.setMinimumSize(200, 200)
        self.layout.addWidget(button)

        button = QPushButton("3")
        button.setFixedSize(80, 20)
        self.layout.addWidget(button)

        # print(self._list)
        # self.show()
    



class Holder(QWidget):

    def __init__(self):
        super().__init__(parent=None)
        self.container = QScrollArea(self)
        self.container.setWidget(Window())

        self.resize(1000, 600)
        self.show()

    def resizeEvent(self, a0):
        self.container.resize(self.size())




import sys
app = QApplication(sys.argv)
window = Holder()
exit(app.exec_())