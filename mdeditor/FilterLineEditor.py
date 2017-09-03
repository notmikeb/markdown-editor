import sys
import os.path as op

from PyQt4 import QtGui as QtWidgets
from PyQt4 import QtCore, QtGui
from os.path import isdir

def cleanpath(p):
    if isinstance(p, QtCore.QString):
        p = str(p.toUtf8())
    return op.normpath(op.expanduser(op.expandvars(p)))

class LineEditWithToolButtons(QtWidgets.QLineEdit):
    """ Line edit to which tool buttons (with icons) can be attached.
    """

    def __init__(self, parent):
        QtWidgets.QLineEdit.__init__(self, parent)
        self._leftButtons = []
        self._rightButtons = []

    def addButtonLeft(self, icon, willHaveMenu=False):
        return self._addButton(icon, willHaveMenu, self._leftButtons)

    def addButtonRight(self, icon, willHaveMenu=False):
        return self._addButton(icon, willHaveMenu, self._rightButtons)

    def _addButton(self, icon, willHaveMenu, L):
        # Create button
        button = QtWidgets.QToolButton(self)
        L.append(button)
        # Customize appearance
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(16, 16))
        button.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        # button.setStyleSheet("QToolButton { border: none; padding: 0px; background-color:red;}");
        # Set behavior
        button.setCursor(QtCore.Qt.ArrowCursor)
        button.setPopupMode(button.InstantPopup)
        # Customize alignment
        if willHaveMenu:
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            if sys.platform.startswith('win'):
                button.setText(' ')
        # Update self
        self._updateGeometry()
        return button

    def setButtonVisible(self, button, visible):
        for but in self._leftButtons:
            if but is button:
                but.setVisible(visible)
        for but in self._rightButtons:
            if but is button:
                but.setVisible(visible)
        self._updateGeometry()

    def resizeEvent(self, event):
        QtWidgets.QLineEdit.resizeEvent(self, event)
        self._updateGeometry(True)

    def showEvent(self, event):
        QtWidgets.QLineEdit.showEvent(self, event)
        self._updateGeometry()

    def _updateGeometry(self, light=False):
        if not self.isVisible():
            return

        # Init
        rect = self.rect()

        # Determine padding and height
        paddingLeft, paddingRight, height = 1, 1, 0
        #
        for but in self._leftButtons:
            if but.isVisible():
                sz = but.sizeHint()
                height = max(height, sz.height())
                but.move(1 + paddingLeft,
                         (rect.bottom() + 1 - sz.height()) / 2)
                paddingLeft += sz.width() + 1
        #
        for but in self._rightButtons:
            if but.isVisible():
                sz = but.sizeHint()
                paddingRight += sz.width() + 1
                height = max(height, sz.height())
                but.move(rect.right() - 1 - paddingRight,
                         (rect.bottom() + 1 - sz.height()) / 2)

        # Set padding
        ss = "QLineEdit { padding-left: %ipx; padding-right: %ipx} "
        self.setStyleSheet(ss % (paddingLeft, paddingRight));

        # Set minimum size
        if not light:
            fw = QtWidgets.qApp.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
            msz = self.minimumSizeHint()
            w = max(msz.width(), paddingLeft + paddingRight + 10)
            h = max(msz.height(), height + fw * 2 + 2)
            self.setMinimumSize(w, h)


class PathInput(LineEditWithToolButtons):
    """ Line edit for selecting a path.
    """

    dirChanged = QtCore.pyqtSignal(str)  # Emitted when the user changes the path (and is valid)
    dirUp = QtCore.pyqtSignal()  # Emitted when user presses the up button

    def __init__(self, parent):
        LineEditWithToolButtons.__init__(self, parent)

        # Create up button
        self._upBut = self.addButtonLeft(QtGui.QIcon(QtGui.QPixmap("up.png")))
        self._upBut.clicked.connect(self.dirUp)

        # To receive focus events
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Set completion mode
        self.setCompleter(QtWidgets.QCompleter())
        c = self.completer()
        c.setCompletionMode(c.InlineCompletion)

        # Set dir model to completer
        dirModel = QtWidgets.QDirModel(c)
        dirModel.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        c.setModel(dirModel)

        # Connect signals
        # c.activated.connect(self.onActivated)
        #self.textEdited.connect(self.onTextEdited)
        # self.textChanged.connect(self.onTextEdited)
        # self.cursorPositionChanged.connect(self.onTextEdited)

    def setPath(self, path):
        """ Set the path to display. Does nothing if this widget has focus.
        """
        print("setpath")
        if not self.hasFocus():
            self.setText(path)
            self.checkValid()  # Reset style if it was invalid first

    def checkValid(self):
        # todo: This kind of violates the abstraction of the file system
        # ok for now, but we should find a different approach someday
        # Check
        text = str(self.text().toUtf8())
        dir = cleanpath(text)
        isvalid = text and isdir(dir) and op.isabs(dir)
        # Apply styling
        ss = self.styleSheet().replace('font-style:italic; ', '')
        if not isvalid:
            ss = ss.replace('QLineEdit {', 'QLineEdit {font-style:italic; ')
        self.setStyleSheet(ss)
        # Return
        return isvalid

    def event(self, event):
        # Capture key events to explicitly apply the completion and
        # invoke checking whether the current text is a valid directory.
        # Test if QtGui is not None (can happen when reloading tools)
        if QtGui and isinstance(event, QtGui.QKeyEvent):
            qt = QtCore.Qt
            if event.key() in [qt.Key_Tab, qt.Key_Enter, qt.Key_Return]:
                self.setText(self.text())  # Apply completion
                self.onTextEdited()  # Check if this is a valid dir
                return True
        return LineEditWithToolButtons.event(self, event)

    def onTextEdited(self, dummy=None):
        text = self.text()
        #print("onTextEdited", text)
        if self.checkValid():
            self.dirChanged.emit(cleanpath(text))

    def focusOutEvent(self, event=None):
        """ focusOutEvent(event)
        On focusing out, make sure that the set path is correct.
        """
        #print("focusOutEvent")
        if event is not None:
            QtWidgets.QLineEdit.focusOutEvent(self, event)

        path = self.parent().getTreePath()
        self.setPath(path)


class Config():
    nameFilter = enumerate([])


class NameFilter(LineEditWithToolButtons):
    """ Combobox to filter by name.
    """

    filterChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        LineEditWithToolButtons.__init__(self, parent)

        # Create tool button, and attach the menu
        self._menuBut = self.addButtonRight(QtGui.QIcon(QtGui.QPixmap('tick.png')), True)
        self._menu = QtWidgets.QMenu(self._menuBut)
        self._menu.triggered.connect(self.onMenuTriggered)
        self._menuBut.setMenu(self._menu)
        #
        # Add common patterns
        for pattern in ['*', '*.txt',
                        '*.h *.c *.cpp *.java']:
            self._menu.addAction(pattern)

        # Emit signal when value is changed
        self._lastValue = ''
        self.returnPressed.connect(self.checkFilterValue)
        self.editingFinished.connect(self.checkFilterValue)

        # Ensure the namefilter is in the config and initialize
        config = []
        if 'nameFilter' not in config:
            # config.nameFilter = '!*.pyc'
            pass
        self.setText('*.txt')

    def setText(self, value, test=False):
        """ To initialize the name filter.
        """
        QtWidgets.QLineEdit.setText(self, value)
        if test:
            self.checkFilterValue()
        self._lastValue = value

    def checkFilterValue(self):
        value = self.text()
        if value != self._lastValue:
            self.parent().nameFilter = value
            self._lastValue = value
            self.filterChanged.emit()

    def onMenuTriggered(self, action):
        self.setText(action.text(), True)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    line = NameFilter(None)
    line.show()
    sys.exit(app.exec_())