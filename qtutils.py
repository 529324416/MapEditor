# Qt工具集


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

def openfiles(caption="打开文件",filter="png文件(*.png)", folder="./") -> list:
    '''获取一组文件'''

    filenames, filetypes = QFileDialog.getOpenFileNames(None, caption=caption, filter=filter, directory=folder)
    if filenames is None or len(filenames) == 0:
        return None
    return filenames

def information(parent=None, title="消息框", content="确认"):

    QMessageBox.information(parent, title, content, QMessageBox.Ok)

def question(parent=None, title="询问框", content="是否确认"):
    '''询问框'''

    return QMessageBox.question(parent, title, content, QMessageBox.Ok|QMessageBox.No) == QMessageBox.Ok


def question_withcancel(parent=None, title="询问框", content="是否确认"):
    '''附带取消特性的询问框'''
    
    return QMessageBox.question(parent, title, content, QMessageBox.Ok|QMessageBox.No|QMessageBox.Cancel)