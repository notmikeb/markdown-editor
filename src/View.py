'''
Created on 05/nov/2013

@author: <luca.restagno@gmail.com>
'''

import MarkdownHighlighter, Constants, Model, Controller
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtWebKit import QWebView
from PyQt4.QtCore import pyqtSlot,SIGNAL,SLOT
import os, platform, subprocess
from PyQt4 import QtCore, QtGui, uic
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import FilterLineEditor


mwin, bwin = uic.loadUiType("mdtree_ui.ui")

class myLeftPanel(mwin, bwin):
    datasignal = QtCore.pyqtSignal(QStringList, name= "datasignal(QStringList)")
    def __init__(self):
        super(myLeftPanel, self).__init__()
        self.setupUi(self)
        self.show()
        self.model = QtGui.QFileSystemModel()
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries) 
        self.model.setNameFilters(QStringList(["*.md", "*.txt", "*.log"]))
        self.model.setNameFilterDisables(False)
		
        print(QDir.currentPath())
		
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)
        self.proxymodel.setDynamicSortFilter(True)
        #self.proxymodel.setFilterRegExp(QString("*.txt"))
        #self.proxymodel.setFilterRegExp(QRegExp(".txt", Qt.CaseInsensitive,QRegExp.FixedString))
        self.proxymodel.setFilterKeyColumn(0)
        self.tree_dir.setModel(self.model)
        self.model.setRootPath("")
        self.tree_dir.resize(QSize(100, self.tree_dir.height()))
        for i in range(1, self.model.columnCount()):
            self.tree_dir.hideColumn(i)
        self.connect(self.box_favorite, QtCore.SIGNAL("currentIndexChanged(QString)"), 
        self.on_change_favorite)
        self.connect(self.btn_addfavorite, QtCore.SIGNAL("clicked()"),
                     self.on_add_favorite)
        self.filtereditor = FilterLineEditor.NameFilter(self)
        self.vlayout.addWidget(self.filtereditor)
        self.patheditor = FilterLineEditor.PathInput(self)
        self.vlayout.addWidget(self.patheditor)

        self.patheditor.dirChanged.connect(self.on_change_inputpath)
        self.connect(self.tree_dir, QtCore.SIGNAL("clicked(QModelIndex)"), self.on_change_dirpath)
    def getTreePath(self):
        filepath = QDir.currentPath()
        indexes = self.tree_dir.selectionModel().selectedIndexes()
        #print ("getTreePath ", str(len(indexes)))
        if len(indexes) > 0:
            filepath = self.model.filePath(indexes[len(indexes)-1])
            filepath = os.path.normcase(str(filepath.toUtf8()))
        return filepath

    def on_change_dirpath(self, index):
        #change inputpath to the new selected folder
        if isinstance(index, QModelIndex):
            filepath = self.model.filePath(index)
            filepath = os.path.normcase(str(filepath.toUtf8()))
            self.patheditor.setText(filepath)

    def on_change_inputpath(self, newpath):
        # change tree_dir to the new path
        if not isinstance(newpath, QString):
            newpath = QString(newpath)
        index = self.model.index(QString(newpath))
        self.tree_dir.scrollTo(index)
        self.tree_dir.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    @property
    def nameFilter(self):
        return self._nameFilter

    @nameFilter.setter
    def nameFilter(self, value):
        print(value, type(value))
        self.model.setNameFilters(QStringList(value.split(" ")))
        self._nameFilter = value

    def btn_doubleclicked_check(self, index):
        print("double click")
        d = index.data()
        if len(d.toString()) > 0:
            print(d.toString())
    def load_favorite(self):
        pass
    def on_change_favorite(self, folderpath):
        print(folderpath)
        qmi = self.model.index(folderpath)
        if qmi:
            self.tree_dir.expand(qmi)
            self.tree_dir.scrollTo(qmi)
            self.tree_dir.selectionModel().select(qmi, QItemSelectionModel.SelectCurrent)
    def on_add_favorite(self):
        indexes = self.tree_dir.selectionModel().selectedIndexes()
        exist = False
        if len(indexes) > 0 and self.model.isDir(indexes[0]):
            filepath = self.model.filePath(indexes[0])
            for i in range(self.box_favorite.count()):
                if filepath == self.box_favorite.itemText(i):
                    exist = True
                    break
            if not exist:
                self.box_favorite.addItem(filepath)
                datalist = []
                for i in range(self.box_favorite.count()):
                    datalist.append(self.box_favorite.itemText(i))
                self.datasignal.emit(datalist)


class myTextEdit(QtGui.QTextEdit):
        
    def wheelEvent(self, event):
        
        numDegrees = event.delta() / 8;
        numSteps = -( numDegrees / 15 );
        
        scrollbar = self.verticalScrollBar()
        step = scrollbar.pageStep() / 10
        
        document_h = self.document().size().height()
        
        preview = self.preview
        h = preview.page().mainFrame().contentsSize().height()
        
        ratio = h / document_h
        
        s = preview.page().mainFrame().scrollPosition().y()
        
        new_value = s + step * numSteps * ratio
        if new_value < 0:
            new_value = 0

        #preview.scroll( 0 , new_value )
        #preview.page().mainFrame().scroll(0, new_value )
        preview.page().mainFrame().setScrollPosition(QtCore.QPoint(0, new_value ))
        
        s = scrollbar.value()
        new_value = s + step * numSteps
        if new_value < 0:
            new_value = 0
        
        scrollbar.setValue( new_value )
        
        preview.reload()
        
        event.accept()


class View(QtGui.QMainWindow):
    openexist = QtCore.pyqtSignal(QtCore.QString, name = "openexist(QtCore.QString)")

    def __init__(self):
        super(View, self).__init__()
        
        _widget = QtGui.QWidget()

        self.isMac = False
        self.ctrlText = 'Ctrl'
        if platform.system() == "Darwin":
            self.isMac = True
            self.ctrlText = 'Cmd'
        
        self.initUI(_widget)
        self.setDockOptions(
            QMainWindow.AllowNestedDocks
            | QMainWindow.AllowTabbedDocks
            # |  QtWidgets.QMainWindow.AnimatedDocks
        )

        # Create floater for shell
        self._shellDock = dock = QDockWidget(self)
        self._shellLayout = QHBoxLayout()
        self._pte_code = QPlainTextEdit()
        dock.setFeatures(dock.DockWidgetMovable)
        dock.setObjectName('code')
        dock.setWindowTitle('code')
        self._shellLayout.addWidget(self._pte_code)
        self._pte_code.setMidLineWidth(20)
        self._pte_code.appendPlainText(QString("1\n2\n3\n"))
        dock.setWidget(self._pte_code)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

        font = QtGui.QFont();
        font.setFamily( Constants.EDIT_FONT );
        font.setStyleHint(QtGui.QFont.Monospace);
        font.setFixedPitch(True);
        font.setPointSize(20);
        self._pte_code.setFont( font )
        self._pte_code.setEnabled(False)
        self._pte_code.setReadOnly(True)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        self.acceptDrops()
        if e.mimeData().hasUrls():
            e.accept()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()
            if len(url) > 0:
                filename = url[0].toLocalFile()
                self.openexist.emit(QString(filename))
        print("dropevent")
        
    @pyqtSlot()
    def scroll(self):
        
        inputEdit = self.active_input()
        scrollbar = inputEdit.verticalScrollBar()
        scroll_pos = scrollbar.value()
        
        document_h = inputEdit.document().size().height()
        
        ratio = scroll_pos / document_h
        
        preview = self.active_preview()
        h = preview.page().mainFrame().contentsSize().height()
        
        preview.scroll( 0 , ratio * h )
        preview.page().mainFrame().scroll(0, ratio * h )
        preview.page().mainFrame().setScrollPosition(QtCore.QPoint(0, ratio * h ))
        
    def add_tab(self, title):
        tab = QtGui.QWidget()
        
        inputEdit = myTextEdit()
        MarkdownHighlighter.MarkdownHighlighter( inputEdit )
        font = QtGui.QFont();
        font.setFamily( Constants.EDIT_FONT );
        font.setStyleHint(QtGui.QFont.Monospace);
        font.setFixedPitch(True);
        font.setPointSize(10);
        inputEdit.setFont( font )
        inputEdit.setTabStopWidth(20)
        
        inputEdit.setGeometry(0,0,200,200)
        inputEdit.setMinimumWidth(100)
        preview = QWebView()
        preview.setGeometry(0,200,200,200)
        inputEdit.preview = preview
        preview.hide()
        
        scrollbar = inputEdit.verticalScrollBar()
        scrollbar.connect(scrollbar,SIGNAL("valueChanged()"),self,SLOT("scroll()"))
        scrollbar.connect(scrollbar,SIGNAL("rangeChanged()"),self,SLOT("scroll()"))
        scrollbar.connect(scrollbar,SIGNAL("sliderPressed()"),self,SLOT("scroll()"))
        scrollbar.connect(scrollbar,SIGNAL("sliderMoved()"),self,SLOT("scroll()"))
        scrollbar.connect(scrollbar,SIGNAL("sliderReleased()"),self,SLOT("scroll()"))
        scrollbar.connect(scrollbar,SIGNAL("actionTriggered()"),self,SLOT("scroll()"))
        
        self.tabs.addTab(tab,title)
        #self.tabs.setWindowTitle('PyQt QTabWidget Add Tabs and Widgets Inside Tab')
        self.connect(inputEdit, SIGNAL("cursorPositionChanged()"), lambda : self.on_cursorPositionChange(inputEdit))

        splitter = QtGui.QSplitter()
        tab_hbox = QtGui.QHBoxLayout()
        
        splitter.addWidget(inputEdit)
        splitter.addWidget(preview)
        # splitter in the middle
        splitter.setSizes([splitter.width()/2, splitter.width()/2])
        tab_hbox.addWidget(splitter)
        tab.setLayout(tab_hbox)
        
        return [inputEdit, preview]

    def on_cursorPositionChange(self, sender):
        if sender != None:
            c = sender.textCursor()
            if c != None:
                self.update_status("Line: " + str(c.blockNumber()+1) + " Column:" + str(c.columnNumber() + 1))
                c.select(QTextCursor.LineUnderCursor)
                linestring = c.selectedText()
                self.update_code(linestring)

    def update_code(self, line):
        self._pte_code.setStatusTip(line)
        data = line.split("|")
        self._pte_code.clear()
        if len(data)> 2:
            self._pte_code.appendPlainText(data[2].simplified())
            if data[2].simplified().endsWith("=") and len(data) > 3:
                self._pte_code.appendPlainText(data[3].simplified())
        else:
            self._pte_code.appendPlainText(line)

    def remove_tab(self, index):
        self.tabs.removeTab(index)
        
    def initUI(self, widget):
        
        hbox = QtGui.QHBoxLayout()

        self.panel_left = myLeftPanel()

        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.splitter = QSplitter()

        self.splitter.addWidget(self.panel_left)
        #self.panel_left.setMaximumWidth(200)
        self.splitter.addWidget(self.tabs)
        self.splitter.setSizes([300 + self.width()/10, 1000])
        hbox.addWidget(self.splitter)
        widget.setLayout(hbox)
        self.panel_left.tree_dir.doubleClicked.connect(self.on_doubleclicked_file)
        
        self.setCentralWidget(widget)
        
        self.makeMenubar() 
        
        self.update_status('Ready')
        
        self.resize(800, 600)
        self.showMaximized()
        #self.showFullScreen()
        self.center()
        self.setWindowTitle( Constants.APP_TITLE )
        self.setWindowIcon(QtGui.QIcon('images/applications-internet.png'))  
    
        self.show()
        
        # Preferences Panel
        self.prefs = QtGui.QWidget()
        self.prefs.resize(500, 150)
        self.prefs.setWindowTitle('Preferences')
        
        formLayout = QtGui.QFormLayout()
        self.browserLineEdit = QtGui.QLineEdit()
        self.browserLineEdit.setReadOnly(True)
        
        self.browserButton = QtGui.QPushButton("&Select")
        
        rowLayout = QtGui.QHBoxLayout()
        
        rowLayout.addWidget(QtGui.QLabel("Preview browser"))
        rowLayout.addWidget(self.browserLineEdit)
        rowLayout.addWidget(self.browserButton)
        
        formLayout.addRow(rowLayout)
        
        self.prefs.setLayout(formLayout)

    def on_doubleclicked_file(self, index):
        oldfilepath = ""
        indexs = self.panel_left.tree_dir.selectionModel().selectedIndexes()
        for i in [indexs[0]]:
            newfilepath = self.panel_left.model.filePath(i)
            if newfilepath != oldfilepath and not os.path.isdir(newfilepath):
                if  str(newfilepath.toLower().toLocal8Bit()).endswith( tuple([".md",".txt"]) ):
                    print(newfilepath)
                self.openexist.emit(QString(newfilepath))
            filepath = newfilepath
        # send a action to
        #self.openexist.emit( QString(filepath))
        pass

    def update_status(self, status):
        self.statusBar().showMessage( status )
        
    def makeMenubar(self):
        
        self.newAction = QtGui.QAction(QtGui.QIcon('images/document-new.png'), '&New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New ('+self.ctrlText+'+N)')
        
        self.openAction = QtGui.QAction(QtGui.QIcon('images/document-open.png'), '&Open', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open file ('+self.ctrlText+'+O)')
        
        self.saveAction = QtGui.QAction(QtGui.QIcon('images/document-save.png'), '&Save', self)
        self.saveAction.setDisabled(True)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save ('+self.ctrlText+'+S)')
        
        self.exportHTMLAction = QtGui.QAction(QtGui.QIcon('images/export-html.gif'), '&Export to HTML', self)
        self.exportHTMLAction.setDisabled(True)
        self.exportHTMLAction.setShortcut('Ctrl+H')
        self.exportHTMLAction.setStatusTip('Export to HTML ('+self.ctrlText+'+H)')
        
        self.viewInBrowserAction = QtGui.QAction(QtGui.QIcon('images/internet-web-browser.png'), '&Browser preview', self)
        self.viewInBrowserAction.setDisabled(True)
        self.viewInBrowserAction.setShortcut('Ctrl+P')
        self.viewInBrowserAction.setStatusTip('Browser preview ('+self.ctrlText+'+P)')
        
        self.showInFolderAction = QtGui.QAction(QtGui.QIcon('images/folder-move.png'), '&Open file folder', self)
        self.showInFolderAction.setDisabled(True)
        self.showInFolderAction.setShortcut('Ctrl+F')
        self.showInFolderAction.setStatusTip('Open file folder ('+self.ctrlText+'+F)')
        
        self.exitAction = QtGui.QAction(QtGui.QIcon('images/application-exit.png'), '&Exit', self)        
        self.exitAction.setShortcut('Alt+F4')
        self.exitAction.setStatusTip('Exit application (Alt+F4)')
        self.exitAction.triggered.connect(QtGui.qApp.quit)
        
        self.boldAction = QtGui.QAction(QtGui.QIcon('images/format-text-bold.png'), '&Bold', self)        
        self.boldAction.setShortcut('Ctrl+B')
        self.boldAction.setStatusTip('Bold ('+self.ctrlText+'+B)')
        self.boldAction.triggered.connect(self.text_make_bold)
        
        self.italicAction = QtGui.QAction(QtGui.QIcon('images/format-text-italic.png'), '&Italic', self)        
        self.italicAction.setShortcut('Ctrl+I')
        self.italicAction.setStatusTip('Italic ('+self.ctrlText+'+I)')
        self.italicAction.triggered.connect(self.text_make_italic)

        self.showToggleAction = QtGui.QAction(QtGui.QIcon('images/format-text-italic.png'), '&Markdown', self)
        self.showToggleAction.setShortcut('Ctrl-M')
        self.showToggleAction.setStatusTip('Markdown'+self.ctrlText+'+M)')
        self.showToggleAction.triggered.connect(self.toggle_webview)
        
        self.quoteAction = QtGui.QAction(QtGui.QIcon('images/quote-left.png'), '&Quote', self)
        if self.isMac is True:
            self.quoteAction.setShortcut('Ctrl+G')
            self.quoteAction.setStatusTip('Quotes ('+self.ctrlText+'+G)')
        else:
            self.quoteAction.setShortcut('Ctrl+Q')
            self.quoteAction.setStatusTip('Quotes ('+self.ctrlText+'+Q)')
        self.quoteAction.triggered.connect(self.text_make_quote)
        
        self.codeAction = QtGui.QAction(QtGui.QIcon('images/code.png'), '&Code', self)        
        self.codeAction.setShortcut('Ctrl+K')
        self.codeAction.setStatusTip('Code ('+self.ctrlText+'+K)')
        self.codeAction.triggered.connect(self.text_make_code)
        
        self.toolbar = self.addToolBar('File actions')
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.showToggleAction)
        
        self.toolbar2 = self.addToolBar('Editor actions')
        
        self.toolbar2.addAction(self.boldAction)
        self.toolbar2.addAction(self.italicAction)
        self.toolbar2.addAction(self.quoteAction)
        self.toolbar2.addAction(self.codeAction)
        
        self.toolbar3 = self.addToolBar('Export actions')
        
        self.toolbar3.addAction(self.exportHTMLAction)
        self.toolbar3.addAction(self.viewInBrowserAction)
        self.toolbar3.addAction(self.showInFolderAction)
        
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        
        fileMenu.addAction(self.exitAction)
        
        self.mapper = QtCore.QSignalMapper(self)
        self.recentDocumentMenu = QtGui.QMenu('&Recent documents', self)
        self.recentDocumentMenu.setDisabled(True)
        
        fileMenu.insertMenu(self.exitAction, self.recentDocumentMenu)
        
        fileMenu.insertSeparator(self.exitAction)
        
        actionsMenu = menubar.addMenu('&Actions')
        actionsMenu.addAction(self.boldAction)
        actionsMenu.addAction(self.italicAction)
        actionsMenu.addAction(self.quoteAction)
        actionsMenu.addAction(self.codeAction)
        actionsMenu.insertSeparator(self.exportHTMLAction)
        actionsMenu.addAction(self.exportHTMLAction)
        actionsMenu.addAction(self.viewInBrowserAction)
        actionsMenu.addAction(self.showInFolderAction)
        actionsMenu.addAction(self.showToggleAction)
        
        toolsMenu = menubar.addMenu('&Tools')
        
        self.themesMapper = QtCore.QSignalMapper(self)
        self.themesMenu = QtGui.QMenu('&Themes', self)
        
        self.preferencesAction = QtGui.QAction(QtGui.QIcon('images/system-run.png'), '&Preferences', self)        
        self.preferencesAction.setShortcut('F7')
        self.preferencesAction.setStatusTip('Preferences')
        
        self.syntaxAction = QtGui.QAction(QtGui.QIcon(), '&Syntax reference', self)
        self.syntaxAction.setStatusTip('Syntax reference')
        
        self.aboutAction = QtGui.QAction(QtGui.QIcon(''), '&About', self)        
        self.aboutAction.setStatusTip('About')
        self.aboutAction.triggered.connect(self.dialog_about)
        
        toolsMenu.addAction(self.preferencesAction)
        toolsMenu.addAction(self.syntaxAction)
        toolsMenu.addAction(self.aboutAction)
        toolsMenu.insertMenu(self.preferencesAction, self.themesMenu)
        
    def show_preferences(self):
        self.prefs.show()
        
    def text_make_quote(self):
        inputEdit = self.active_input()
        cursor = inputEdit.textCursor()
        textSelected = cursor.selectedText()
        cursor.insertText( "\n> "+textSelected )
    
    def text_make_bold(self):
        self.format_text( "**" )
        
    def text_make_italic(self):
        self.format_text( "*" )
        
    def text_make_code(self):
        self.format_text( "`" )
            
    def format_text(self, character):
        inputEdit = self.active_input()
        cursor = inputEdit.textCursor()
        textSelected = cursor.selectedText()
        cursor.insertText( character + textSelected + character )
        if len(textSelected) == 0:
            cursor.setPosition( cursor.position() - len(character) )
            inputEdit.setTextCursor(cursor)
        
    def add_recent_document(self, file_path):
        recentFileAction = QtGui.QAction('&'+str(file_path), self)
        self.mapper.setMapping(recentFileAction, str(file_path))
        self.recentDocumentMenu.addAction(recentFileAction)
        return recentFileAction
    
    def add_theme_menu_item(self, name, theme_index):
        themeAction = QtGui.QAction('&'+str(name), self)
        self.themesMapper.setMapping(themeAction, str(theme_index))
        self.themesMenu.addAction(themeAction)
        return themeAction
        
    def center(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def set_document(self, document):
        inputEdit = self.active_input()
        inputEdit.setText( QtCore.QString(document) )
        
    def get_current_document_content(self):
        inputEdit = self.active_input()
        return unicode(inputEdit.toPlainText())
        
    def select_file(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Select file', "", "*.md")
        print( "Selected file: " + fname )
        if fname:
            return fname
        else:
            return False
        
    def save_file_picker(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save file', "", "*.md")
        print( "Selected file: " + fname )
        if fname:
            return fname
        else:
            return False
        
    def select_browser(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Select browser', "", "*.exe")
        if fname:
            return fname
        else:
            return False

    def active_input(self):
        return self.tabs.currentWidget().findChildren(QtGui.QTextEdit)[0]
    
    def active_preview(self):
        return self.tabs.currentWidget().findChildren(QWebView)[0]

    def toggle_webview(self):
        a = self.tabs.currentWidget().findChildren(QWebView)[0]
        if not a.isHidden():
            a.hide()
        else:
            a.show()
        print(type(a), repr(a))
    
    def change_active_tab(self, index):
        self.tabs.setCurrentIndex(index)
        
    def no_file_alert(self):
        QtGui.QMessageBox.warning(self, "Alert", "The file does not exist")
        
    def dialog_about(self):
        QtGui.QMessageBox.about(self, "About", "<b>Markdown Editor</b><br>version "+Constants.VERSION+"<br><br>Author: "+Constants.AUTHOR+"<br><br>License: "+Constants.LICENSE)
        
    def open_folder(self, path):
        print "open folder: "+ str(path)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    def load_favorite(self, pathlist):
        ql = QtCore.QStringList(pathlist)
        self.panel_left.box_favorite.clear()
        self.panel_left.box_favorite.addItems(pathlist)
            