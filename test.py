import sys
from PyQt5.QtWidgets import QApplication
from euclid import EuclidContainer, EuclidButton, EuclidLabel

class NewLabel(EuclidLabel):

    def __init__(self, size: tuple):
        super().__init__(size=size)

class NewButton(EuclidButton):
    def __init__(self, size: tuple):
        super().__init__(size=size)



class Window(EuclidContainer):

    def __init__(self):
        super().__init__(size=(1, 1))
        self.resize(1000, 600)
        

        btnsize = (100, 30)
        btn1 = NewButton(btnsize)
        btn1.setText("1")
        btn2 = NewButton(btnsize)
        btn2.setText("2")
        btn3 = NewButton(btnsize)
        btn3.setText("3")

        self.addh(btn1)
        self.addh(btn2)
        self.add(btn3)

        self.container = EuclidContainer(size=(0.5, 300))
        self.addh(self.container)

        label = NewLabel(size=(1, 1))
        label.setStyleSheet("background-color:#434e57;")
        self.container.add(label)

        self.show()


app = QApplication(sys.argv)
window = Window()
exit(app.exec_())