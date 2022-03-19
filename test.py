# import sys
# from euclid import *
# from PyQt5.QtMultimediaWidgets import QVideoWidget
# from PyQt5.QtMultimedia import QMediaPlayer

# class MyWindow(QWidget):

#     def __init__(self):
#         super().__init__(None)

#         self.window = EuclidWindow(title="测试窗体", parent=self)
#         self.window.add(EuclidButton(title="测试1"))
#         self.window.addh(EuclidButton(title="测试2"))
#         self.window.addh(EuclidButton(title="测试3"))

#         self.resize(1000, 600)
#         self.show()

# app = QApplication(sys.argv)
# app.setStyleSheet(EUCLID_DEFAULT_STYLE)
# window = MyWindow()
# exit(app.exec_())


import numpy as np
x = np.full((4,4), 2)
x[2, 2] = 4
print(np.any(x == 3))