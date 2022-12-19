from PyQt5.QtCore import QSize, QPoint
from PyQt5.QtWidgets import QWidget



EUCLID_MAINWINDOW = "EuclidMainWindow"
EUCLID_WINDOW = "EuclidWindow"
EUCLID_WINDOW_ALPHA = "EuclidWindowAlpha"
EUCLID_CONTAINER = "EuclidContainer"
EUCLID_CONTAINER_ALPHA = "EuclidContainerAlpha"
EUCLID_AREA = "EuclidArea"
EUCLID_AREA_ALPHA = "EuclidAreaAlpha"
EUCLID_CIRCLE_BUTTON = "EuclidCircleButton"
EUCLID_TITLEBAR = "EuclidTitleBar"
EUCLID_TITLEBAR_CONTENT = "EuclidTitleContent"
EUCLID_TITLEBAR_CLOSEBTN = "EuclidCloseButton"
EUCLID_TITLEBAR_LOCKBTN_NORMAL = "EuclidLockButtonNormal"
EUCLID_TITLEBAR_LOCKBTN_LOCKED = "EuclidLockButtonLocked"
EUCLID_TITLEBAR_TOPBTN_NORMAL = "EuclidTopButtonNormal"
EUCLID_SIZEGRIP = "EuclidSizeGrip"


# euclid widgets
EUCLID_BUTTON = "EuclidButton"
EUCLID_BUTTON_RED = "EuclidButtonRed"
EUCLID_BUTTON_DISABLE = "EuclidButtonDisable"

EUCLID_LABEL = "EuclidLabel"
EUCLID_LABEL_ERROR = "EuclidLabelError"
EUCLID_LABEL_WARNING = "EuclidLabelWarning"
EUCLID_LABEL_SUCCESS = "EuclidLabelSuccess"

EUCLID_SUBAREA = "EuclidSubArea"
EUCLID_SUBAREA_CONTAINER = "EuclidSubAreaContainer"
EUCLID_LISTVIEW = "EuclidListView"
EUCLID_ROUND_PICTUREBOX = "EuclidRoundPictureBox"
EUCLID_LINEEDITOR = "EuclidLineEditor"

EUCLID_DIALOG = "EuclidDialog"

EUCLID_MINIINDICATOR = "EuclidMiniIndicator"
EUCLID_MINIINDICATOR_RUN = "EuclidMiniIndicatorRun"
EUCLID_MINIINDICATOR_INVALID = "EuclidMiniIndicatorInvalid"

EUCLID_IMAGE = "EuclidImage"
EUCLID_IMAGE_NONBORDER = "EuclidImageNonBorder"

EUCLID_COMBOBOX = "EuclidComboBox"
EUCLID_VIEW = "EuclidView"




class EuclidGeometry:

    @staticmethod
    def fullsizeGap(gapsize:tuple) -> callable:
        return lambda x:QSize(x.width() - gapsize[0], x.height() - gapsize[1])

    @staticmethod
    def fullsizeGapX(gapx:int) -> callable:
        return lambda x:QSize(x.width() - gapx, x.height())

    @staticmethod
    def fullsizeGapY(gapy:int) -> callable:
        return lambda x:QSize(x.width(), x.height() - gapy)

def halfsize(size):
    return QSize(int(size.width() / 2),int(size.height() / 2))

def move_window(window: QWidget, evt, pos: QPoint):
    '''drag window by mouse when mouse is moving
    compute the offset from mouse moving, and add to window 
    @window: a widget
    @evt: QMouseMoveEvent, this function must be called in mouseMoveEvent
    @pos: the position of mouse click '''

    offset = evt.pos() - pos            # get mouse offset
    window.move(window.pos() + offset)
    window.parent().update()

def resize_window(window: QWidget, evt, pos: QPoint):
    '''adjust window size by sizegrip button, button would 
    record the offset of mosue move, and send to window 
    for adjusting size
    @window: target window
    @evt: QMouseMoveEvent
    @pos: the position of mouse click'''

    offset = evt.pos() - pos
    window.resize(window.width() + offset.x(), window.height() + offset.y())
    window.parent().update()

def restyle(element: QWidget, name):
    '''change the object name of target widget
    and refresh the style'''

    element.setObjectName(name)
    element.style().unpolish(element)
    element.style().polish(element)