from PyQt4 import QtCore, QtGui, uic
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

mwin, bwin = uic.loadUiType("mdtree_ui.ui")


class mywin(mwin, bwin):
    def __init__(self):
        super(mywin, self).__init__()
        self.setupUi(self)
        self.show()
        model = QtGui.QFileSystemModel()
        print(QDir.currentPath())
        self.tree_dir.setModel(model)
        self.tree_dir.doubleClicked .connect(self.btn_doubleclicked_check)

    def btn_doubleclicked_check(self, index):
        print("double click")
        d = index.data()
        if len(d.toString()) > 0:
            print(d.toString())
        pass

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    m1 = mywin()
    m1.show()
    sys.exit(app.exec_())