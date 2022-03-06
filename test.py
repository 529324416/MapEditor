import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont
from euclid import *
from euclid import _EuclidLabel
import random

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
        self.window = EuclidWindow(parent=self, title="测试窗体")
        self.window.resize(200, 300)

        # for i in range(20):
        #     btn = EuclidButton(size=(80, 20))
        #     btn.setText(str(i))
        #     if random.random() > 0.5:
        #         self.window._container.add(btn)
        #     else:
        #         self.window._container.addh(btn)
        btn = EuclidButton(size=(80, 20))
        btn.set_callback(lambda:btn.adjust_size(QSize(80, 80)))
        self.window._container.addh(btn)
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        self.window._container.add(EuclidButton(size=(80, 20)))
        
        # resizefunc = lambda x: QSize(75, x.height() - 5)
        # _container = self.window._container.addcontainerh(resizefunc=resizefunc)
        # for i in range(10):
        #     _container.add(EuclidButton(size=(80, 20)))
        # self.window._container.addh(EuclidButton(size=(80, 20)))

        # self.window2 = EuclidWindow(parent=self, has_title=False)
        # self.window2.resize(200, 250)

        restore_window_status("./test.json")
        

    def closeEvent(self, a0):
        store_window_status(EuclidWindow.window_list, "./test.json")


app = QApplication(sys.argv)
font = QFont("zpix", 9)
font.setStyleStrategy(QFont.NoAntialias)
app.setFont(font)
window = Window()
exit(app.exec_())