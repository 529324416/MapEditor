

# from Euclid.EuclidWindow import EuclidWindow
# from Euclid.EuclidWidgets import EuclidButton

# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from utils import *
# import sys
# import time

# class MyWindow(QMainWindow):

#     def __init__(self):
#         super().__init__(None)
#         self.resize(1000,600)
#         self.scene = QGraphicsScene()
#         self.view = QGraphicsView(self)
#         self.view.resize(self.size())
#         self.view.setScene(self.scene)

#         self.pixmap = QPixmap("./Res/agent_anchor.png").scaledToWidth(200)
#         self.painter = QPainter(self.pixmap)

#         self.item = QGraphicsPixmapItem(self.pixmap)
#         self.scene.addItem(self.item)
#         self.items = list()

#     def keyPressEvent(self, ev: QKeyEvent) -> None:
#         if ev.key() == Qt.Key_B:
#             print("尝试绘制|追加新的pixmap")
#             smallpixmap = QPixmap("./Res/penicon.png")
#             s = time.time()
#             for i in range(10000):
#                 item = QGraphicsPixmapItem(smallpixmap)
#                 self.items.append(item)
#                 self.scene.addItem(item)
#                 item.setPos(i * 10, 0)
#             print(time.time() - s)
#             print(len(self.scene.children()))
#             print(len(self.items))

#         elif ev.key() == Qt.Key_C:
#             print("尝试绘制|在pixmap上绘制pixmap")
#             smallpixmap = QPixmap("./Res/penicon.png")
#             s = time.time()
#             for i in range(10000):

#                 self.painter.drawPixmap(QRect(0, 0, 30, 30), smallpixmap)
#                 self.item.setPixmap(self.pixmap)
#             print(time.time() - s)
            
#         return super().keyPressEvent(ev)



# app = QApplication(sys.argv)
# window = MyWindow()
# window.show()
# exit(app.exec_())

import numpy as np
x = np.array([
    [1,2,3],
    [0,0,0],
    [4,2,0]
])
y = np.copy(x[1:2,:])
y[0,0] = 10
print(y)
print(x)