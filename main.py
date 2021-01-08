# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


# SYSTEM modules
import sys
import ast
import traceback
import webbrowser
from os import getcwd
from time import sleep
from datetime import datetime
from platform import platform as _platform, python_version  # for logging only
from PyQt5 import QtCore, QtGui

# APP modules
import common
from prefs import PrefsDialog, ConstDialog
from prefs import constants, cstmConstVars, cvNameMax, cvValueMax
from singleton import SingleApplication
from mathfuncs import MathError
from mathfuncs import safeeval_dict     # Custom funcs and redefined funcs from 'math' module
from parsefuncs import *                # Expression IO parse functions


platform = sys.platform[:3]

# WINDOWS modules and GLOBALS
if platform == 'win':
    import winkeypress
    from ctypes import WinDLL, windll
    from winglobalkey import GlobalHotKeys


###################
#  -  GLOBALS  -  #
###################

# Copy of default safeeval_dict namespace for suggestions
# (safeeval_dict may be extended by const/vars)
safeeval_Default = sorted(safeeval_dict)

translate = QtWidgets.QApplication.translate
QT_TRANSLATE_NOOP = QtCore.QT_TRANSLATE_NOOP

appname = 'SUM'
version = '0.5b'

firstStartMsg_NL = QT_TRANSLATE_NOOP('FirstStart', '''
<font size=4><b>First Start</b></font>
<p>
<b>NumLock</b> key on keyboard is identified,<br />
and set as default <i>Global Shortcut Key</i>.<br />
<br />
If there is neither Numeric keypad<br />
nor <b>NumLock</b> key on your keyboard,<br />
you should change <i>Global Shortcut Key</i><br />
in <b>Preferences</b> dialog.<br />
Use Menu button (the rightmost one)<br />
or <b>Ctrl+P</b> key combination.<br />
</p>
<p>
Note: Using NumLock key as a shortcut<br />
will keep Numeric keypad always on!
''')

firstStartMsg = QT_TRANSLATE_NOOP('FirstStart', '''
<font size=4><b>First Start</b></font>
<p>
One of key features of SUM calculator<br />
is system-wide <i>Global Shortcut Key</i>.<br />
<br />
Unfortunately, Global shortcut assignment<br />
is currently available for Windows only.<br />
In case of another OS, you should try<br />
to use system-specific approach instead.
''')


# '%' and '^' are also not allowed, but have special notification
# see percCheck() and oldpowCheck()
notAllowedItems = ['=', '<', '>', '@', '&', '?', '|', '[', ']', '{', '}', '\'', '\\',
                   '"', '~', ':', ';', '$', '`', '#']

syntaxErrorItems = ['not in', 'in', 'is', 'else', 'elif', 'if', 'for', 'or', 'os',
                    'and', 'pass', 'continue', 'break', 'return', 'while', 'try',
                    'finally', 'lambda', 'assert', 'class', 'def', 'del', 'from',
                    'raise', 'global', 'nonlocal', 'yield', 'False', 'True',
                    'None', 'import', 'width', 'not', 'as']

notAllowedNodes = {
                   'And': 'and',
                   'For': 'for',
                   'Import': 'import',
                   'Is': 'is',
                   'In': 'in',
                   'NotIn': 'not in',
                   'IsNot': 'is not',
                   'Lambda': 'lambda',
                   'Not': 'not',
                   'Or': 'or',
                }

typeErrors = ['\'int\' object is not callable',
              '\'float\' object is not callable',]

specFuncs = ['bin', 'oct', 'hex']
specTypes = ['0b', '0o', '0x']


###################
#  -  CLASSES  -  #
###################

class TupleError(SyntaxError):

    'Raise un exception if Tuple (,) node found'

    def __init__(self, offset):
        self.offset = offset


class ComplexError(SyntaxError):

    'Raise un exception if Complex number (i.e. 1.24j) found'

    def __init__(self, num):
        self.num = num


class NodeError(NameError):

    'Raise un exception if "name" in notAllowedNodes.'

    def __init__(self, name):
        self.name = name


class NodeCheck(ast.NodeVisitor):

    def visit_Call(self, node):
        'Check for Call (function) node.'
        pass

    def visit_Tuple(self, node):
        raise TupleError(node.col_offset)

    def visit_Num(self, node):
        if isinstance(node.n, complex):
            raise ComplexError(str(node.n))

    def visit_Name(self, node):
        'Check for Name (any string) node.'
        if node.id in sorted(constants) + sorted(cstmConstVars):
            pass
        else:
            raise NodeError(node.id)

    def visit_Del(self, node):
        raise NodeError('del')

    def visit_Import(self, node):
        raise NodeError('import')

    def visit_Lambda(self, node):
        raise NodeError('lambda')

    def visit_Or(self, node):
        raise NodeError('or')

    def visit_For(self, node):
        raise NodeError('for')

    def visit_And(self, node):
        raise NodeError('and')

    def visit_Is(self, node):
        raise NodeError('is')

    def visit_In(self, node):
        raise NodeError('in')

    def visit_Not(self, node):
        raise NodeError('not')

    def visit_NotIn(self, node):
        raise NodeError('not')

    def visit_IsNot(self, node):
        raise NodeError('is')

    def visit_If(self, node):
        raise NodeError('if')


class BalloonWidget(QtWidgets.QWidget):

    '''
    Notification balloon widget (inherits QWidget),
    using to show hints and error messages.
    Appearing right above QLineEdit main widget,
    with anchor points passed to show().
    '''

    def __init__(self, parent=None):
        super(BalloonWidget, self).__init__(flags=QtCore.Qt.Popup)

        self.screenW = QtWidgets.QApplication.desktop().availableGeometry().width()
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.outInfo = QtWidgets.QLabel(self)
        self.setMouseTracking(True)
        self.setStyleSheet('''
                           QWidget {
                                    background-color: #ffffe1;
                                    padding: 5px;
                                    }
                           ''')

    def show(self, text, tfont, coord):
        'Overloaded method extended with additional args.'
        self.outInfo.setText(text)
        self.outInfo.setFont(tfont)
        self.outInfo.show()
        self.adjustSize()
        rightEdge = coord.x() + self.size().width()

        if rightEdge > self.screenW:
            self.move(coord.x() - (rightEdge - self.screenW),
                      coord.y() - self.size().height() - tfont.pointSize()//2)
        else:
            self.move(coord.x(),
                      coord.y() - self.size().height() - tfont.pointSize()//2)

        self.setVisible(True)

    def keyPressEvent(self, e):
        'Overloaded method'
        if self.isVisible():
            self.close()
            mainWindow.lineedit.keyPressEvent(e)

    def mousePressEvent(self, e):
        'Overloaded method'
        if self.isVisible():
            self.close()
            mainWindow.mousePressEvent(e)

    def mouseMoveEvent(self, event):
        'Overloaded method'
        if self.isVisible():
            self.close()


class MyLineedit(QtWidgets.QLineEdit):
    '''
    Inheriting QLineEdit with overloaded keyPressEvent(),
    mousPressEvent() functions, and Autocopy indicator icon
    installed as a QToolbutton.
    All custom keyPress events defined in this class.
    '''
    def __init__(self, widget, parent=None):
        super(MyLineedit, self).__init__(parent)

        self.widget = widget

        self.button = QtWidgets.QToolButton(self)
        self.button.setCursor(QtCore.Qt.ArrowCursor)

        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.button.setFixedSize(self.widget.iconSize, self.widget.iconSize)
        self.button.setStyleSheet('QWidget {border: None; padding: 0px}')

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.button, 0, QtCore.Qt.AlignRight)

        if platform == 'win':
            self.layout.setContentsMargins(0, 0, 2, 0)
            self.setFixedHeight(self.widget.buttonsSize - 2)
        else:
            self.layout.setContentsMargins(0, 0, 3, 0)
            self.setFixedHeight(self.widget.buttonsSize)

        self.setTextMargins(0, 0, int(self.widget.iconSize * 1.125), 0)

        self.expKeys = {
            QtCore.Qt.Key_Plus: '+',
            QtCore.Qt.Key_Minus: '-',
            QtCore.Qt.Key_Slash: '/',
            QtCore.Qt.Key_Asterisk: '*',
            }

        self.moveKeys = [
            QtCore.Qt.Key_Left,
            QtCore.Qt.Key_Right,
            QtCore.Qt.Key_Home,
            QtCore.Qt.Key_End,
            ]

    def tooltip(self, status, path, tip=''):
        self.button.setToolTip(translate('Tooltip', 'Autocopy is {0}').format(tip))
        self.button.setIconSize(QtCore.QSize(self.widget.iconSize, self.widget.iconSize))
        if status:
            self.button.setIcon(QtGui.QIcon(path + 'clipboard-on.png'))
        else:
            self.button.setIcon(QtGui.QIcon(path + 'clipboard-off.png'))

    # ALL LineEdit key events
    def keyPressEvent(self, e):
        # Symbols no matter what keyboard layout is using
        nvk = (48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 110,
               186, 187, 188, 189, 190, 191, 192,
               219, 220, 221, 222, 226)
        if common._eq_done is True:
            if e.modifiers() == QtCore.Qt.ControlModifier:
                if e.key() == QtCore.Qt.Key_H:
                    self.widget.browserOpenClose()
                elif e.key() == QtCore.Qt.Key_Up:
                    self.widget.switchToHistory()
                elif e.key() == QtCore.Qt.Key_Down:
                    self.widget.switchToLine()
                elif e.key() == QtCore.Qt.Key_Left:
                    self.setText(self.widget.lineedit.text().split(' = ')[0])
                    super(MyLineedit, self).keyPressEvent(e)
                    common._eq_done = False
                elif e.key() == QtCore.Qt.Key_Right:
                    self.setText(self.widget.lineedit.text().split(' = ')[1])
                    common._eq_done = False
                elif e.key() == QtCore.Qt.Key_Backspace:
                    self.clear()
                    common._eq_done = False
                elif e.key() == QtCore.Qt.Key_X and self.hasSelectedText():
                    self.widget.lineedit.cut()
                    self.setText(self.widget.lineedit.text().split(' = ')[0])
                    common._eq_done = False
                elif e.key() == QtCore.Qt.Key_C and self.hasSelectedText():
                    self.widget.lineedit.copy()
                elif e.key() == QtCore.Qt.Key_S:
                    self.widget.saveHistory()
                    self.widget.baloonShow(translate('Balloon', '<b>History is saved!</b>\
                        (it is always automatically saving on Exit)'))

            elif e.key() == QtCore.Qt.Key_Return or\
                    e.key() == QtCore.Qt.Key_Enter:
                pass
            elif e.key() in self.expKeys:
                self.setText(self.widget.lineedit.text().split(' = ')[1] + self.expKeys[e.key()])
                common._eq_done = False
                common._listing_on = False
            elif e.text().isalnum() or e.nativeVirtualKey() in nvk:
                self.clear()
                super(MyLineedit, self).keyPressEvent(e)
                common._eq_done = False
                common._listing_on = False
            elif e.key() == QtCore.Qt.Key_Delete or\
                    e.key() == QtCore.Qt.Key_Escape:
                self.clear()
                common._eq_done = False
            elif e.key() == QtCore.Qt.Key_Home:
                self.setText(self.widget.lineedit.text().split(' = ')[0])
                self.home(False)
                common._eq_done = False
            elif e.key() == QtCore.Qt.Key_End:
                self.setText(self.widget.lineedit.text().split(' = ')[1])
                self.end(False)
                common._eq_done = False
                common._listing_on = False
            elif e.key() == QtCore.Qt.Key_Up:
                self.widget.historyUp()
                common._eq_done = False
            elif e.key() == QtCore.Qt.Key_Left or\
                    e.key() == QtCore.Qt.Key_Backspace:
                self.setText(self.widget.lineedit.text().split(' = ')[0])
                common._eq_done = False
            elif e.key() == QtCore.Qt.Key_Right:
                self.setText(self.widget.lineedit.text().split(' = ')[1])
                common._eq_done = False
        else:
            if e.modifiers() == QtCore.Qt.ControlModifier:
                if e.key() == QtCore.Qt.Key_H:
                    self.widget.browserOpenClose()
                elif e.key() == QtCore.Qt.Key_Up:
                    self.widget.switchToHistory()
                elif e.key() == QtCore.Qt.Key_Down:
                    self.widget.switchToLine()
                elif e.key() == QtCore.Qt.Key_Backspace:
                    self.widget.lineedit.setText(
                        self.widget.lineedit.text()[self.widget.lineedit.cursorPosition():])
                    self.widget.lineedit.home(False)
                elif e.key() == QtCore.Qt.Key_Delete:
                    self.widget.lineedit.setText(
                        self.widget.lineedit.text()[:self.widget.lineedit.cursorPosition()]
                        )
                elif e.key() == QtCore.Qt.Key_X and self.hasSelectedText():
                    self.widget.lineedit.cut()
                    common._listing_on = False
                elif e.key() == QtCore.Qt.Key_C:
                    if self.hasSelectedText():
                        self.widget.lineedit.copy()
                    elif self.widget.listView.selectionModel().hasSelection():
                        self.widget.copyExprOrValue()
                elif e.key() == QtCore.Qt.Key_R:
                    self.widget.copyResult()

                elif e.key() == QtCore.Qt.Key_V:
                    self.widget.lineedit.paste()
                    common._listing_on = False
                elif e.key() == QtCore.Qt.Key_S:
                    self.widget.saveHistory()
                    self.widget.baloonShow(translate('Balloon', '<b>History is saved!</b>\
                        (it is always automatically saving on Exit)'))
                else:
                    super(MyLineedit, self).keyPressEvent(e)

            elif e.key() == QtCore.Qt.Key_Up:
                if not self.widget.lineedit.text() or common._listing_on:
                    self.widget.historyUp()
            elif e.key() == QtCore.Qt.Key_Down:
                if not self.widget.lineedit.text() or common._listing_on:
                    self.widget.historyDown()
            elif e.key() == QtCore.Qt.Key_Delete:
                if self.widget.listView.selectionModel().hasSelection():
                    if self.widget.lineedit.cursorPosition() == len(self.widget.lineedit.text()):
                        if self.widget.model.rowCount() == 1:
                            self.widget.lineedit.clear()
                        self.widget.del_item()
                    else:
                        common._listing_on = False
                        super(MyLineedit, self).keyPressEvent(e)
                        self.widget.listView.selectionModel().clear()
                else:
                    super(MyLineedit, self).keyPressEvent(e)
            elif e.key() == QtCore.Qt.Key_Escape:
                if self.hasSelectedText():
                    self.deselect()
                else:
                    self.widget.listView.selectionModel().clear()
                    self.widget.lineedit.clear()
                    common._listing_on = False
            else:
                if e.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                    super(MyLineedit, self).keyPressEvent(e)
                elif e.text().isalnum() or e.nativeVirtualKey() in nvk or \
                         e.key() == QtCore.Qt.Key_Backspace:
                    common._listing_on = False
                    self.widget.listView.selectionModel().clear()
                    super(MyLineedit, self).keyPressEvent(e)
                else:
                    super(MyLineedit, self).keyPressEvent(e)

    def mousePressEvent(self, e):
        if common._eq_done is True and\
                e.button() == QtCore.Qt.LeftButton:
            temp = self.widget.lineedit.text().split(' = ')[0]
            self.setText(temp)
            common._eq_done = False
        super(MyLineedit, self).mousePressEvent(e)


class MainWindow(QtWidgets.QWidget):
    '''
    Main UI of the application.
    No PyQt designer (ui) file imported,
    all DESIGN and behaviour is defined in this class.
    See mainCalcFunc() function.
    '''
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Defining Desktop and 'Available'(w/o Taskbar) screen resolution
        self.desktop = QtWidgets.QApplication.desktop()
        self.availScreen = self.desktop.availableGeometry()
        self.screenW, self.screenH = self.availScreen.width(), self.availScreen.height()

        self._want_to_close = False
        self.on = translate('ToolTip', 'On')
        self.off = translate('ToolTip', 'Off')
        self.invInput = translate('Balloon', '<b>Invalid input:</b> ')

        self.fontSizeRaw = self.font().pointSize()
        self.ffamily = 'MS Shell Dlg'

        self.moved_or_resized = True

        # -------- #
        # SETTINGS #
        # -------- #
        self.settings = QtCore.QSettings('settings.ini', QtCore.QSettings.IniFormat)
        self.historyFile = 'history.txt'

        # Initial settings last saved if available
        self.readSettings()

        # Set clipboard
        self.cboard = QtWidgets.QApplication.clipboard()

        # UI Variables/Constants
        self.setMinimumSize(self.minW, self.minH)
        self.mainH = self.buttonsSize + (2 * self.m)    # Define mainLayout height
        self.windowOpenH = self.minH
        self.comboMake()

        # Defining Main Window DEFAULT size W:H and origin L:T (Left-Top)
        self.defaultW, self.defaultH = int(self.minW * 1.5), self.minH
        self.defaultL, self.defaultT = self.screenW - self.defaultW, self.screenH - self.defaultH

        # App icons
        self.app_icon = QtGui.QIcon('./icons/sum.ico')
        self.setWindowIcon(self.app_icon)

        # -------- #
        # DESIGNER #
        # -------- #
        # Main Window elements
        self.listView = QtWidgets.QListView()
        self.model = QtGui.QStandardItemModel(self.listView)
        self.model.setColumnCount(1)
        self.loadHistory()
        self.lineedit = MyLineedit(self)
        self.listButton = QtWidgets.QPushButton()
        self.settButton = QtWidgets.QToolButton()
        if platform == 'dar':
            self.listButton = QtWidgets.QToolButton()
        self.listView.setModel(self.model)

        self.listView.setAlternatingRowColors(True)
        self.listView.setWordWrap(True)
        self.listView.setFocusProxy(self.lineedit)
        self.listButton.setFixedSize(self.buttonsSize, self.buttonsSize)
        self.listButton.setCheckable(True)

        self.settButton.setFixedSize(self.buttonsSize, self.buttonsSize)
        self.settButton.setShortcut(QtCore.Qt.ControlModifier + QtCore.Qt.Key_M)
        self.settButton.setStyleSheet('QToolButton::menu-indicator{image: none}')
        self.settButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.listButton.setFocusPolicy(QtCore.Qt.NoFocus)

        if self.browserIsOpened:
            self.listButton.setChecked(True)
        else:
            self.listButton.setChecked(False)

        self.listButton.setIcon(QtGui.QIcon(self.iconPath + 'list.png'))
        self.listButton.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        self.settButton.setIcon(QtGui.QIcon(self.iconPath + 'menu.png'))
        self.settButton.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.setFont(QtGui.QFont(self.ffamily, self.fontSize))
        self.lineedit.setFont(QtGui.QFont(self.ffamily, self.fontSize))


        # Main Window Layout
        self.maxLayout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.lineedit)
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.listButton)
        self.buttonLayout.addWidget(self.settButton)
        self.buttonLayout.setSpacing(self.m // 2 - 2)
        self.mainLayout.addItem(self.buttonLayout)
        self.mainLayout.setSpacing(self.m // 2)
        self.maxLayout.addWidget(self.listView)
        self.maxLayout.addItem(self.mainLayout)
        self.maxLayout.setContentsMargins(self.m, self.m, self.m, self.m)
        self.maxLayout.setSpacing(self.m)
        self.setLayout(self.maxLayout)

        # Main Window Menu
        self.settMenu = QtWidgets.QMenu()
        self.menuAutocopy = self.settMenu.addAction(translate('Menu',
                                                              'Autocopy result'),
                                                    self.checkAutoCopy, 'Ctrl+Shift+C')
        self.menuAutocopy.setCheckable(True)
        if self.autoCopy:   # Initialize on start
            self.menuAutocopy.setChecked(True)
            self.lineedit.tooltip(self.autoCopy, self.iconPath, self.on)
        else:
            self.menuAutocopy.setChecked(False)
            self.lineedit.tooltip(self.autoCopy, self.iconPath, self.off)
        self.settMenu.addSeparator()
        self.menuPrf = self.settMenu.addAction(translate('Menu', 'Preferences...'),
                                                self.prefsDialog, 'Ctrl+P')

        self.menuAbt = self.settMenu.addAction(translate('Menu', 'About'),
                                               self.aboutDialog)
        self.menuHlp = self.settMenu.addAction(translate('Menu', 'Help'),
                                               self.helpOpen, 'F1')
        self.settMenu.addSeparator()
        self.menuExt = self.settMenu.addAction(translate('Menu', 'Exit'),
                                               self.exitApp, 'Ctrl+E')
        self.settButton.setMenu(self.settMenu)
        self.settButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        # ------------ #
        # END Designer #
        # ------------ #

        # Init Geometry
        if not self.browserIsOpened:
            self.listView.setVisible(False)
            self.setMinimumSize(self.minW, self.mainH)
            self.setMaximumSize(self.screenW, self.mainH)
        self.move(self.settings.value('pos', QtCore.QPoint(self.defaultL - 30, self.defaultT)))
        self.resize(self.settings.value('size', QtCore.QSize(self.defaultW, self.defaultH)))

        # Main Window Signals
        self.lineedit.returnPressed.connect(self.mainCalcFunc)
        self.listButton.clicked.connect(self.browserOpenClose)
        self.listView.selectionModel().currentChanged.connect(self.listView_rowchanged)
        self.listView.customContextMenuRequested.connect(self.listContextMenu)

        # Constants Init
        self.constDialog = ConstDialog()
        self.constDialog.setWindowIcon(self.app_icon)
        self.constDialog.inputLine.setFont(QtGui.QFont(self.ffamily, self.fontSize))
        self.constDialog.listView.setFont(QtGui.QFont(self.ffamily, self.fontSize))

        # Systray init
        self.tray = SystemTrayIcon(self.app_icon, self)
        self.trayTooltip()

        # ErrorBalloon init
        self.errorbaloon = BalloonWidget()

        # Init Lang
        self.qtTranslator = QtCore.QTranslator()
        self.appTranslator = QtCore.QTranslator()
        self.applyTranslator()

    ###########################
    # END - Main UI __Init__ #
    # #########################

    def hkeyThreadStart(self):
        self.hkeyThread = HotkeyListener(self, self.key1, self.key2)
        self.hkeyThread.start()
        self.hkeyThread.hkPressed.connect(self.hotkeyCommand)

    def nlockThreadStart(self):
        self.nlockThread = NumLockActivator(self)

    def saveMessageBox(self, title, text):
        t = translate('MessageBox',
            '\nThe program may require permissions to write to its current location.\
            \nYou should place it to a non-system folder so it can run properly.')
        QtWidgets.QMessageBox.warning(self, title, text + t)

    def loadHistory(self):
        f = QtCore.QFile(self.historyFile)
        if f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            stream = QtCore.QTextStream(f)
            stream.setCodec('UTF-8')
            line = stream.readLine()
            while line:
                item = QtGui.QStandardItem(line)
                item.setEditable(False)
                self.model.appendRow(item)
                line = stream.readLine()
            f.close()
        else:
            pass

    def saveHistory(self):
        f = QtCore.QFile(self.historyFile)
        line = QtCore.QByteArray()
        if f.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            for row in range(self.model.rowCount()):
                line.append((self.model.data(self.model.index(row, 0)) + '\n').encode('UTF-8'))
            f.write(line)
            f.close()
        else:
            self.saveMessageBox(translate('MessageBox', 'History'),
                                translate('MessageBox',
                                          'Unable to save \'{0}\' file!\n'.format(self.historyFile)))

    def applyTranslator(self):
        # Load Translators
        self.qtTranslator.load('./langs/qtbase_' + self.lang[:2])
        self.appTranslator.load('./langs/sumcalc_' + self.lang[:2])
        QtWidgets.qApp.installTranslator(self.qtTranslator)
        QtWidgets.qApp.installTranslator(self.appTranslator)
        self.deg = translate('WindowTitle', 'degrees')
        self.rad = translate('WindowTitle', 'radians')
        # Reinitialize changing widgets
        self.on = translate('ToolTip', 'On')
        self.off = translate('ToolTip', 'Off')
        if self.autoCopy:   # Initialize on start
            self.lineedit.tooltip(self.autoCopy, self.iconPath, self.on)
        else:
            self.lineedit.tooltip(self.autoCopy, self.iconPath, self.off)
        self.invInput = translate('Balloon', '<b>Invalid input:</b> ')
        self.setWindowTitle('{0} {1}    [ {2} ]'.format(
                    appname,
                    version,
                    self.rad if common._use_radians else self.deg))
        self.listButton.setToolTip(translate('Tooltips', 'History (Ctrl+H)'))
        self.settButton.setToolTip(translate('Tooltips', 'Menu (Ctrl+M)'))
        self.menuPrf.setText(translate('Menu', 'Preferences...'))
        self.menuAbt.setText(translate('Menu', 'About'))
        self.menuHlp.setText(translate('Menu', 'Help'))
        self.menuExt.setText(translate('Menu', 'Exit'))
        self.tray.exitBtn.setText(translate('Tray', 'Exit'))
        self.menuAutocopy.setText(translate('Menu', 'Autocopy result'))
        self.constDialog.setWindowTitle(translate('ConstVarDialog', 'Constants and Variables'))
        self.constDialog.statBar.setText(translate('ConstVarDialog',
                                                   'Add new constant or variable.<br />Pattern: '
                                                   '<b>name</b> ({0}) = <b>value</b> ({1})').format(cvNameMax, cvValueMax))
        self.constDialog.infoNote.setText(translate('ConstVarDialog',
                                                    'Temporary (unchecked) variable assignment<br />'
                                                    'is available by the main calculation field.'))
        self.constDialog.warnNote.setText(translate('ConstVarDialog',
                                                    'Note: All unchecked fields '
                                                    'get lost on Exit.'))

    def reinitUI(self):
        self.hide()
        self.setMinimumSize(self.minW, self.minH)
        self.mainH = self.buttonsSize + (2 * self.m)
        self.defaultW, self.defaultH = int(self.minW * 1.5), self.minH
        self.defaultL, self.defaultT = self.screenW - self.defaultW, self.screenH - self.defaultH
        self.listButton.setFixedSize(self.buttonsSize, self.buttonsSize)
        self.settButton.setFixedSize(self.buttonsSize, self.buttonsSize)
        if platform == 'win':
            self.lineedit.setFixedHeight(self.buttonsSize - 2)
            self.lineedit.layout.setContentsMargins(0, 0, 2, 0)
        else:
            self.lineedit.setFixedHeight(self.buttonsSize)
            self.lineedit.layout.setContentsMargins(0, 0, 3, 0)
        self.listButton.setIcon(QtGui.QIcon(self.iconPath + 'list.png'))
        self.listButton.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        self.settButton.setIcon(QtGui.QIcon(self.iconPath + 'menu.png'))
        self.settButton.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        self.updateFontSize()

        self.buttonLayout.setSpacing(self.m // 2 - 2)
        self.mainLayout.setSpacing(self.m // 2)
        self.maxLayout.setContentsMargins(self.m, self.m, self.m, self.m)
        self.maxLayout.setSpacing(self.m)
        self.windowOpenH = self.minH
        if not self.browserIsOpened:
            self.listView.setVisible(False)
            self.setMinimumSize(self.minW, self.mainH)
            self.setMaximumSize(self.screenW, self.mainH)
        self.lineedit.button.setFixedSize(self.iconSize, self.iconSize)
        self.lineedit.setTextMargins(0, 0, int(self.iconSize * 1.125), 0)
        self.lineedit.tooltip(self.autoCopy, self.iconPath,
                              tip=self.on if self.autoCopy else self.off)
        if self.pos().y() + self.frameGeometry().height() > self.screenH:
            self.move(self.pos().x(), self.screenH - self.frameGeometry().height())
        if self.pos().x() + self.frameGeometry().width() > self.screenW:
            self.move(self.screenW - self.frameGeometry().width(), self.pos().y())
        self.show()

    def updateFontSize(self):
        self.lineedit.setFont(QtGui.QFont(self.ffamily, self.fontSize))
        self.listView.setFont(QtGui.QFont(self.ffamily, self.fontSize))

    def aboutDialog(self):
        aboutText = translate('About', '''
            <font size=4><b>{a}</b>
            Calculator</font><br />
            <font size=3><i>Stop Using Mouse!</i></font>
            <p>Version: {ver}<br />
            <a href="https://github.com/qandak/sumcalc">GitHub</a> Homepage</p>
            <p>{a} <i></i> is an advanced cross-platform<br />
            one-line GUI calculator based on<br />
            Python interpreter and Qt framework.<br />
            (Python v{py} {pl}, PyQt v{qt})</p>
            <p>
            <a href="http://www.gnu.org/licenses/gpl.html">GPL</a> License<br />
            Copyright © 2016 Levon Melikyan<br />
            <a href="mailto:lmelikyan@gmail.com">lmelikyan@gmail.com</a></p>
            ''')
        QtWidgets.QMessageBox.about(self,
                                translate('About', 'About'),
                                aboutText.format(a=appname,
                                                ver=version,
                                                py=python_version(),
                                                pl=sys.platform,
                                                qt=QtCore.qVersion()))

    def helpOpen(self):
        dir = getcwd()
        if '\\' in dir:
            dir.replace('\\', '/')
        helpUrl = 'file:///{d}/help/{ln}/html/index.html'.format(d=dir, ln=self.lang[:2])
        webbrowser.open_new_tab(helpUrl)

    def prefsDialog(self):
        self.prefs = PrefsDialog()
        self.prefs.setWindowIcon(self.app_icon)
        # Read values
        if self.lang.startswith('ru'):
            self.prefs.uiLangSelect.setCurrentIndex(1)
        else:
            self.prefs.uiLangSelect.setCurrentIndex(0)
        if self.uiDouble:
            self.prefs.uiResSelect.setCurrentIndex(1)
        else:
            self.prefs.uiResSelect.setCurrentIndex(0)
        self.prefs.fontSize.setValue(self.fontSizeRaw)
        self.prefs.calcScient.setChecked(common._scientific_on)
        self.prefs.angDegrees.setChecked(not common._use_radians)
        self.prefs.angRadians.setChecked(common._use_radians)
        self.prefs.hstReformat.setChecked(common._reformat_on)
        self.prefs.startMinimized.setChecked(common._start_minimized)
        self.prefs.hstAdd.setChecked(self.histSave)
        self.prefs.hstAutoClear.setChecked(self.histDelOnExit)
        self.prefs.hstCount.setValue(self.histMax)
        if platform == 'win':
            self.prefs.globKey1.setCurrentIndex(self.key1)
            self.prefs.globKey2.setCurrentIndex(self.key2)
        else:
            self.prefs.globKey1.setDisabled(True)
            self.prefs.globKey2.setDisabled(True)
            self.prefs.globNote.setText(translate('Prefs',
                'Note: Global shortcuts work in Windows only,\n\
                you should use system-specific approach instead.'))
        if not self.histSave:
            self.prefs.hstCount.setDisabled(True)
        self.prefs.hstClear.clicked.connect(self.historyClearConfirm)
        # Init and Show dialog
        self.prefs.buttons.accepted.connect(self.acceptPrefs)
        self.prefs.buttons.rejected.connect(self.rejectPrefs)
        self.prefs.constButton.clicked.connect(self.constDialogShow)
        self.prefs.restBtn.clicked.connect(self.resetAllConfirm)
        self.prefs.setFixedSize(self.prefs.sizeHint())
        self.prefs.setModal(True)
        self.prefs.show()

    def acceptPrefs(self):
        # Set changed settings
        lg = self.prefs.languages[self.prefs.uiLangSelect.currentText()]
        if lg[:2] != self.lang[:2]:
            self.lang = lg
            self.applyTranslator()
        self.uiDouble = self.prefs.uiResSelect.currentIndex()
        common._scientific_on = self.prefs.calcScient.isChecked()
        common._use_radians = self.prefs.angRadians.isChecked()
        common._reformat_on = self.prefs.hstReformat.isChecked()
        common._start_minimized = self.prefs.startMinimized.isChecked()
        self.histSave = self.prefs.hstAdd.isChecked()
        self.histDelOnExit = self.prefs.hstAutoClear.isChecked()
        self.histMax = self.prefs.hstCount.value()
        diff = self.model.rowCount() - self.histMax
        # Make changes
        if diff > 0:
            self.model.removeRows(0, diff)
        if platform == 'win':
            if self.key2 != self.prefs.globKey2.currentIndex():
                if self.prefs.globKey2.currentIndex() == 0:
                    self.nlockThreadStart()
                else:
                    self.nlockThread.stop()
                self.key1 = self.prefs.globKey1.currentIndex()
                self.key2 = self.prefs.globKey2.currentIndex()
                self.hkeyThread.stop()
                self.hkeyThreadStart()

                self.comboMake()
                self.trayTooltip()
        else:
            self.prefs.globKey1.setDisabled(True)
            self.prefs.globKey2.setDisabled(True)

        if self.uiDouble and self.iconSize == 16:
            self.makeUiDouble()
            self.reinitUI()
        else:
            if self.iconSize == 32:
                self.makeUiNormal()
                self.reinitUI()

        if self.prefs.fontSize != self.fontSizeRaw:
            self.fontSizeRaw = self.prefs.fontSize.value()
            self.fontSize = self.fontSizeRaw * (2 if self.uiDouble else 1)
            self.updateFontSize()

        self.setWindowTitle('{0} {1}    [ {2} ]'.format(
                            appname,
                            version,
                            self.rad if common._use_radians else self.deg))
        self.writeSettings()
        self.saveHistory()
        self.prefs.hstCountSet()
        self.prefs.close()

    def rejectPrefs(self):
        self.prefs.close()

    def readSettings(self):
        self.lang = self.settings.value('lang', QtCore.QLocale.system().name(), type=str)
        self.uiDouble = self.settings.value('uidouble', False, type=bool)
        self.fontSizeRaw = self.settings.value('fsraw', self.font().pointSize(), type=int)
        if self.uiDouble:
            self.makeUiDouble()
        else:
            self.makeUiNormal()
        common._use_radians = self.settings.value('radians', False, type=bool)
        common._scientific_on = self.settings.value('sciennot', True, type=bool)
        common._reformat_on = self.settings.value('reformat', True, type=bool)
        common._start_minimized = self.settings.value('startmin', False, type=bool)
        self.histSave = self.settings.value('historysave', True, type=bool)
        self.histDelOnExit = self.settings.value('histdelonexit', False, type=bool)
        self.histMax = self.settings.value('histmax', 100, type=int)
        if platform == 'win':
            if self.checkNumLock():
                self.key1 = self.settings.value('key1', 0, type=int)
                self.key2 = self.settings.value('key2', 0, type=int)
                if self.key2 == 0:
                    self.nlockThreadStart()  # create virtual NumLock activator
            else:
                if self.settings.value('key2', 0, type=int) == 0:
                    self.key1 = 1
                    self.key2 = 11
                else:
                    self.key1 = self.settings.value('key1', 1, type=int)
                    self.key2 = self.settings.value('key2', 11, type=int)
            self.hkeyThreadStart()   # if 'win' - always create Hotkey thread
        else:
            self.key1 = self.settings.value('key1', 0, type=int)
            self.key2 = self.settings.value('key2', 0, type=int)

        self.windowOpenH = self.settings.value('browserHeight', self.minH, type=int)
        self.browserIsOpened = self.settings.value('historystatus', False, type=bool)
        self.autoCopy = self.settings.value('autocopy', True, type=bool)

    def writeSettings(self):
        if not common._reset_settings:
            try:
                self.settings.setValue('lang', self.lang)
                self.settings.setValue('radians', common._use_radians)
                self.settings.setValue('sciennot', common._scientific_on)
                self.settings.setValue('reformat', common._reformat_on)
                self.settings.setValue('startmin', common._start_minimized)
                self.settings.setValue('uidouble', self.uiDouble)
                self.settings.setValue('fsraw', self.fontSizeRaw)
                self.settings.setValue('histmax', self.histMax)
                self.settings.setValue('historysave', self.histSave)
                self.settings.setValue('histdelonexit', self.histDelOnExit)
                self.settings.setValue('key1', self.key1)
                self.settings.setValue('key2', self.key2)
                self.settings.setValue('size', self.size())
                self.settings.setValue('pos', self.pos())
                self.settings.setValue('historystatus', self.browserIsOpened)
                self.settings.setValue('browserHeight', self.windowOpenH)
                self.settings.setValue('autocopy', self.autoCopy)
            except:
                self.saveMessageBox(translate('MessageBox', 'Preferences'),
                                    translate('MessageBox',
                                              'Unable to save \'settings.ini\' file!\n'))

    def comboMake(self):
        self.comboKey = '{0}{1}{2}'.format(
                                    PrefsDialog.keyList1[self.key1],
                                    '' if self.key1 == 0 else '+',
                                    PrefsDialog.keyList2[self.key2])

    def trayTooltip(self):
        self.tray.setToolTip('{0} {1} ({2})'.format(appname, version, self.comboKey))

    def makeUiDouble(self):
        self.minW = 600
        self.minH = 240
        self.m = 10
        self.buttonsSize = 40
        self.iconPath = './icons/32/'
        self.iconSize = 32
        self.fontSize = self.fontSizeRaw * 2

    def makeUiNormal(self):
        self.minW = 300
        self.minH = 120
        self.m = 6
        self.buttonsSize = 24
        self.iconPath = './icons/16/'
        self.iconSize = 16
        self.fontSize = self.fontSizeRaw

    def historyClearConfirm(self):
        if self.model.rowCount() > 0:
            message = translate('MessageBox',
                                'Are you sure you want to permanently clear all the History?')
            answer = QtWidgets.QMessageBox.question(self.prefs,
                                                translate('MessageBox', 'Clear History',
                                                          'Title - Are you sure...'),
                                                message,
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                    QtWidgets.QMessageBox.No)
            if answer == QtWidgets.QMessageBox.Yes:
                self.model.clear()
            else:
                pass
        else:
            inf = translate('MessageBox', 'History is empty.')
            QtWidgets.QMessageBox.information(self.prefs,
                                          translate('MessageBox', 'Clear History',
                                                    'Title - Is empty...'),
                                          inf)

    def resetAllConfirm(self):
        message = translate('MessageBox',
            'Are you sure you want to reset all preferences and UI settings?<br /><br />\
            <i>Note: Restart needed for reset to take effect!</i>')
        answer = QtWidgets.QMessageBox.question(self.prefs, translate('MessageBox', 'Reset All'),
                                            message,
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if answer == QtWidgets.QMessageBox.Yes:
            self.settings.clear()
            common._reset_settings = True
        else:
            pass

    def checkAutoCopy(self):
        self.needToSaveSettings()
        if self.autoCopy:
            self.menuAutocopy.setChecked(False)
            self.autoCopy = False
            self.lineedit.tooltip(self.autoCopy, self.iconPath, self.off)
        else:
            self.menuAutocopy.setChecked(True)
            self.autoCopy = True
            self.lineedit.tooltip(self.autoCopy, self.iconPath, self.on)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.lineedit.setFocus()

    def resizeEvent(self, e):
        self.needToSaveSettings()

    def moveEvent(self, e):
        self.needToSaveSettings()

    def needToSaveSettings(self):
        if not self.moved_or_resized:
            self.moved_or_resized = True
            QtCore.QTimer.singleShot(3000, self.settingsChanged)

    def settingsChanged(self):
        self.writeSettings()
        self.moved_or_resized = False

    def closeEvent(self, e):
        if self._want_to_close:
            super(MainWindow, self).closeEvent(e)
        else:
            e.ignore()
            self.hide()
            if common._first_minimize:
                text = translate('TrayMessage',
                                 'Use tray icon or \'{ck}\' to restore the application').format(
                                 ck=self.comboKey if platform == 'win' else 'make a shortcut')

                self.tray.showMessage(translate('TrayMessage',
                                                '{0} has been minimized to the notification area').format(appname),
                                      text)
                common._first_minimize = False

    def exitApp(self):
        self._want_to_close = True
        self.writeSettings()
        if self.histDelOnExit:
            self.model.clear()
        self.saveHistory()
        if platform == 'win':
            self.hkeyThread.stop()
            if self.key2 == 0:
                self.nlockThread.stop()
        self.close()

    def listContextMenu(self, pos):

        def copyExpr():
            self.cboard.setText(str(data.split(' = ')[0]))

        def copyRes():
            self.cboard.setText(str(data.split(' = ')[1]))

        def copyValue():
            self.cboard.setText(str(data))

        lstContMenu = QtWidgets.QMenu()
        curIndex = self.listView.indexAt(pos).row()
        if curIndex >= 0:
            data = self.model.data(self.listView.currentIndex())
            if '=' in data:
                lstContMenu.addAction(translate('HistoryCtx',
                                                'Copy expression'),
                                      copyExpr, 'Ctrl+C')
                lstContMenu.addAction(translate('HistoryCtx',
                                                'Copy result'),
                                      copyRes, 'Ctrl+R')
            else:
                lstContMenu.addAction(translate('HistoryCtx',
                                                'Copy value'),
                                      copyValue, 'Ctrl+C')
            lstContMenu.addSeparator()
            lstContMenu.addAction(translate('HistoryCtx',
                                            'Delete'),
                                  self.del_item, 'Del')

            lstContMenu.exec_(self.listView.viewport().mapToGlobal(pos))

    def copyExprOrValue(self):
        data = self.model.data(self.listView.currentIndex())
        self.cboard.setText(str(data.split(' = ')[0]))

    def copyResult(self):
        data = self.model.data(self.listView.currentIndex())
        if '=' in data:
            self.cboard.setText(str(data.split(' = ')[1]))

    def baloonShow(self, message):
        self.errorbaloon.__init__()
        self.errorbaloon.show(message,
                              QtGui.QFont(self.ffamily, self.fontSize),
                              self.mapToGlobal(self.lineedit.pos()))

    def constDialogShow(self):
        self.constDialog.setModal(True)
        self.constDialog.inputLine.setFocus()
        self.constDialog.show()

    def tray_activated(self, reason):
        if reason != QtWidgets.QSystemTrayIcon.Context:
            self.raiseMainWindow()

    def raiseMainWindow(self):
        self.show()
        self.activateWindow()

    # runs on Global Shortcut event only
    def hotkeyCommand(self):
        if self.isHidden() or not self.isActiveWindow():
            self.raiseMainWindow()
        elif self.isActiveWindow():
            self.hide()
        if not self.nlockThread.isRunning():
            self.nlockThread.start()

    # Open History(ListView) by Ctrl+Up combo
    def switchToHistory(self):
        if not self.listView.isVisible():
            self.browserOpenClose()

    # Close History(ListView) by Ctrl+Down combo
    def switchToLine(self):
        if self.listView.isVisible():
            self.browserOpenClose()

    # Browser Closing
    def browserClose(self, size, pos):
        self.listView.setVisible(False)
        self.windowOpenH = self.size().height()
        browserH = self.windowOpenH - self.mainH
        self.setMinimumSize(self.minW, self.mainH)
        self.setMaximumSize(self.screenW, self.mainH)
        self.resize(size.width(), self.mainH)
        self.move(pos.x(), pos.y() + browserH)
        self.browserIsOpened = False
        self.listButton.setChecked(False)

    # Browser Opening
    def browserOpen(self, size, pos):
        browserH = self.windowOpenH - self.mainH
        self.setMinimumSize(self.minW, self.minH)
        self.setMaximumSize(self.screenW, self.screenH)
        # Case when browser placing titlebar higher than screen's top border
        if pos.y() - browserH < 0:
            self.move(pos.x(), 0)
            self.resize(size.width(), size.height() + browserH)
        else:
            self.move(pos.x(), pos.y() - browserH)
            self.resize(size.width(), size.height() + browserH)
        self.listView.setVisible(True)
        self.browserIsOpened = True
        self.listButton.setChecked(True)
        self.listView.setFocusProxy(self.lineedit)

    # Browser open/close switch form listButton click
    def browserOpenClose(self):
        s = self.size()
        p = self.pos()
        if self.listView.isVisible():
            self.browserClose(s, p)
        else:
            self.browserOpen(s, p)

    # Check (for Windows only!) if system keyboard has NumPad (NumLock)
    def checkNumLock(self):
        if platform == 'win':
            if WinDLL("User32.dll").GetKeyState(0x90):
                return True
            else:
                winkeypress.PressKey(0x90)
                winkeypress.ReleaseKey(0x90)
                sleep(0.1)
                return WinDLL("User32.dll").GetKeyState(0x90)
        else:
            return False

    # ListView row selection change
    def listView_rowchanged(self, current, previous):
        if current.data() is not None:
            self.lineedit.setText(current.data().split(' = ')[0])

    # ListView selected row deletion
    def del_item(self):
        self.model.removeRow(self.listView.currentIndex().row())

    # Move UP in history list
    def historyUp(self):
        if self.listView.selectionModel().hasSelection():
            if self.listView.currentIndex().row() > 0:
                current = self.listView.currentIndex().row()
                next = self.model.index(current - 1, 0)
                self.listView.selectionModel().setCurrentIndex(
                    next,
                    QtCore.QItemSelectionModel.ClearAndSelect)
        else:
            index = self.model.index(self.model.rowCount() - 1, 0)
            self.listView.selectionModel().select(
                            index,
                            QtCore.QItemSelectionModel.ClearAndSelect)
            self.listView.selectionModel().setCurrentIndex(
                            index,
                            QtCore.QItemSelectionModel.ClearAndSelect)
            common._listing_on = True

    # Move DOWN in hostory list
    def historyDown(self):
        if self.listView.selectionModel().hasSelection():
            if self.listView.currentIndex().row() < self.model.rowCount() - 1:
                current = self.listView.currentIndex().row()
                next = self.model.index(current + 1, 0)
                self.listView.selectionModel().setCurrentIndex(
                    next,
                    QtCore.QItemSelectionModel.ClearAndSelect)
                common._listing_on = True
            elif self.listView.currentIndex().row() == self.model.rowCount() - 1:
                self.lineedit.clear()
                self.listView.selectionModel().clear()

    def addToHist(self, i):
        if not self.histMax > self.model.rowCount():
            self.model.removeRow(0)
        self.listView.clearSelection()
        i.setEditable(False)
        self.model.appendRow(i)
        self.listView.scrollToBottom()

    def modelManage(self, t, res, saveOn):

        if isinstance(res, str) and\
                any((x in res) for x in specTypes) and t.lower() == res:
            base = (2, 8, 16)
            newRes = 0
            for s in specTypes:    # binary, octal, hexadecimal
                if s in res:
                    newRes = int(res, base[specTypes.index(s)])
            bohDone = '{0} = {1}'.format(reformat(t), newRes)
            index = self.model.index(self.model.rowCount() - 1, 0)
            if saveOn and not bohDone == self.model.data(index):
                item = QtGui.QStandardItem(bohDone)
                self.addToHist(item)
            self.lineedit.setText('{0} = {1}'.format(t, newRes))
            self.lineedit.setSelection(len(t) + 3, len(str(newRes)))
            common._eq_done = True
            common._listing_on = True

        elif is_number(t.strip()) and rd(float(t.strip())) == res:
            numDone = '{0}'.format(res)
            index = self.model.index(self.model.rowCount() - 1, 0)
            if saveOn and not numDone == self.model.data(index):
                item = QtGui.QStandardItem(numDone)
                self.addToHist(item)
            self.lineedit.clear()
        else:
            exprDone = '{0} = {1}'.format(reformat(t), res)
            index = self.model.index(self.model.rowCount() - 1, 0)
            if saveOn and not exprDone == self.model.data(index):
                item = QtGui.QStandardItem(exprDone)
                self.addToHist(item)
            self.lineedit.setText('{0} = {1}'.format(t, res))
            self.lineedit.setSelection(len(t) + 3, len(str(res)))
            common._eq_done = True
            common._listing_on = True

    def assignManage(self, checked):
        errTitle = translate('ConstVarError',
                             '<b>Invalid assignment:</b> ')
        if checked == (1, 0):
            error = translate('ConstVarError',
                              'name or value length is exceeded ({0}, {1})').format(cvNameMax, cvValueMax)
            self.baloonShow(errTitle + error)
        elif checked[0] in cstmConstVars:
            for i in range(self.constDialog.constvarModel.rowCount()):
                n = self.constDialog.constvarModel.data(
                    self.constDialog.constvarModel.index(i, 0)).split('=')[0].strip()
                if checked[0] == n:
                    if self.constDialog.constvarModel.item(i).checkState() == 0:
                        self.constDialog.constvarModel.removeRow(i)
                        self.addVar(*checked, update=True)   # Update existing temporary variable
                    else:
                        error = translate('ConstVarError',
                                          'name <b>{0}</b> is already assigned as a non-temporary '
                                          'variable (see Constants and Variables)').format(checked[0])
                        self.baloonShow(errTitle + error)
                    break

        elif checked[0] in safeeval_dict or checked[0] in constants:
            error = translate('ConstVarError',
                              'name <b>{0}</b> is reserved.').format(checked[0])
            self.baloonShow(errTitle + error)
        else:
            self.addVar(*checked)   # Add new temporary variable

    def addVar(self, *assign, update=False):
        statusU = translate('ConstVar', 'updated')
        statusS = translate('ConstVar', 'saved')
        n, v = assign
        self.lineedit.clear()
        cstmConstVars[n] = eval(str(v))     # 'v' may be string or int/float
        safeeval_dict[n] = eval(str(v))     # 'v' may be string or int/float
        # Add to ConstVarModel
        item = QtGui.QStandardItem('{0}\t=  {1}'.format(*assign))
        item.setEditable(False)
        item.setCheckable(True)
        item.setCheckState(0)   # Unchecked by default
        self.constDialog.constvarModel.appendRow(item)
        note = translate('ConstVar',
                         '<b>{0}</b> = <b>{1} |</b> temporary variable '
                         '<b>{0}</b> is {status}').format(n, v,
                                          status=statusU if update else statusS)
        self.baloonShow(note)
        # Add copy to History
        indexHist = self.model.index(self.model.rowCount() - 1, 0)
        exprDone = '{0} = {1}'.format(*assign)
        if self.histSave and not exprDone == self.model.data(indexHist):
            itemHst = QtGui.QStandardItem(exprDone)
            self.addToHist(itemHst)

    # Check in mainCalcFunc() for '%' symbol
    def percCheck(self, t):
        spl = t.split('%')
        hint = translate('AllowCheck', ' <b>|</b> see <b>pc</b> '
                'and <b>perc</b> functions '
                'for percentage (\'%\' is confusing for long expr.)')
        error = '<font color=red>%</font>'.join(spl) + hint
        self.baloonShow(self.invInput + error)

    # Check in mainCalcFunc() for '^' symbol
    def oldpowCheck(self, t):
        spl = t.split('^')
        hint = translate('AllowCheck', ' <b>|</b> use <b>**</b> (double asterisk) for exponentiation')
        error = '<font color=red>^</font>'.join(spl) + hint
        self.baloonShow(self.invInput + error)

    # Check in mainCalcFunc() for unallowed symbols
    def allowCheck(self, t, it, i):
        error = t[:i] + '<font color=red>' + it + '</font>' + t[i+len(it):]
        self.baloonShow(self.invInput + error)

    # MAIN calculating function
    def mainCalcFunc(self):
        text = self.lineedit.text().lstrip()

        if text:
            allow = True
            savedName = ''

            # Check for '%' sign (spec. notif.)
            if '%' in text:
                allow = False
                self.percCheck(text)

            # Check for '^' sign (spec. notif.)
            if '^' in text and allow:
                allow = False
                self.oldpowCheck(text)

            # Check for assignment
            if '=' in text and allow:
                checked = ConstDialog.checkConstVar(text)
                if checked:
                    if common._expr_tryassign:
                        savedName, text = checked
                    else:
                        allow = False
                        self.assignManage(checked)

            # If no assignment, '=' will be checked in notAllowedItems
            if allow:
                for item in notAllowedItems:
                    if item in text:
                        allow = False
                        self.allowCheck(text, item, text.index(item))
                        break

            if allow:
                try:
                    check = ast.parse(text, mode='eval')
                    NodeCheck().visit(check)

                    result = eval(turnFloat(binOctHex(text, specFuncs, specTypes)), safeeval_dict, {})
                    result = rd(result)

                    if common._expr_tryassign:
                        self.assignManage((savedName, result))
                        common._expr_tryassign = False
                    else:
                        self.modelManage(text, result, self.histSave)

                        if self.autoCopy:
                            self.cboard.setText(str(result))

                except TupleError as te:
                    common._expr_tryassign = False
                    temp = list(text)
                    offset = te.offset
                    tuple_part = text[offset:]
                    if ',' in tuple_part:
                        offset = offset + tuple_part.index(',')
                    temp[offset] = '<font color=red>'+temp[offset]+'</font>'
                    error = ''.join(temp)
                    self.baloonShow('{0} {1}'.format(self.invInput, error))

                except ComplexError as ce:
                    common._expr_tryassign = False
                    temp = list(text)
                    offset = text.lower().index(ce.num) + len(ce.num) - 1
                    temp[offset] = '<font color=red>'+temp[offset]+'</font>'
                    error = ''.join(temp)
                    self.baloonShow('{0} {1}'.format(self.invInput, error))

                except NodeError as nde:
                    common._expr_tryassign = False
                    hint = translate('Hint',
                                     '<b>|</b> append brackets for function call '
                                     '(<b>help</b> inside - Quickhelp)')
                    name = nde.name
                    ind_s = text.index(name)
                    ind_e = ind_s + len(name)
                    if text.count(name) > 1:    # if more than one 'name' in 'text'
                        c = 0
                        for i in range(text.count(name)):
                            end_i = text.index(name, c) + len(name)
                            # if 'name' is substring indexing before
                            if end_i == len(text):
                                ind_s = text.index(name, c)
                                ind_e = ind_s + len(name)
                                break
                            elif text[end_i].isalpha():
                                c = end_i
                                continue
                            elif text.index(name, c) > c:
                                lbefore = text[text.index(name, c)-1]
                                if lbefore.isalnum() or lbefore == '_':
                                    c = end_i
                                    continue
                                else:
                                    ind_s = text.index(name, c)
                                    ind_e = ind_s + len(name)
                                    break
                            else:
                                ind_s = text.index(name, c)
                                ind_e = ind_s + len(name)
                                break

                    suggs = suggest(name, safeeval_Default)
                    error = text[:ind_s] + '<font color=red>' + name + '</font>' + text[ind_e:]
                    self.baloonShow('{0} {1} {2} {h}'.format(
                            self.invInput,
                            error,
                            suggs,
                            h=hint if name in safeeval_Default and
                                      type(safeeval_dict[name]).__name__ == 'function'
                                      else ''))

                except SyntaxError as se:
                    common._expr_tryassign = False
                    offset = turnBack(text, se.text, se.offset)
                    temp = list(text)
                    if text[offset-1].isalpha():
                        name = text[offset-1]
                        for i in syntaxErrorItems:
                            if text[:offset].endswith(i):
                                name = i
                                break
                        ind_s = text.index(name)
                        ind_e = ind_s + len(name)
                        if text.count(name) > 1:    # if more than one 'name' in 'text'
                            c = 0
                            for i in range(text.count(name)):
                                end_i = text.index(name, c) + len(name)
                                # if 'name' is substring indexing before
                                if end_i == len(text):
                                    ind_s = text.index(name, c)
                                    ind_e = ind_s + len(name)
                                    break
                                elif text[end_i].isalpha():
                                    c = end_i
                                    continue
                                elif text.index(name, c) > c:
                                    lbefore = text[text.index(name, c)-1]
                                    if lbefore.isalnum() or lbefore == '_':
                                        c = end_i
                                        continue
                                    else:
                                        ind_s = text.index(name, c)
                                        ind_e = ind_s + len(name)
                                        break
                                else:
                                    ind_s = text.index(name, c)
                                    ind_e = ind_s + len(name)
                                    break
                        suggs = suggest(name, safeeval_Default)
                        error = text[:ind_s]+'<font color=red>'+name+'</font>'+text[ind_e:]
                        self.baloonShow('{0} {1} {2}'.format(self.invInput, error, suggs))
                    else:
                        temp[offset-1] = '<font color=red>'+temp[offset-1]+'</font>'
                        error = ''.join(temp)
                        self.baloonShow(self.invInput + error)

                except NameError as ne:
                    common._expr_tryassign = False
                    temp = list(text)
                    name = str(ne).split('\'')[1]
                    ind_s = text.index(name)
                    ind_e = ind_s + len(name)
                    if text.count(name) > 1:    # if more than one 'name' in 'text'
                        c = 0
                        for i in range(text.count(name)):
                            end_i = text.index(name, c) + len(name)
                            # if 'name' is substring indexing before
                            if ind_s > 0:
                                lbefore = text[text.index(name, c)-1]
                                if lbefore.isalnum() or lbefore == '_':
                                    c = end_i
                                    continue
                                else:
                                    ind_s = text.index(name, c)
                                    ind_e = ind_s + len(name)
                                    break
                            elif ind_s == 0:
                                ind_s = text.index(name, c)
                                ind_e = ind_s + len(name)
                                break
                            else:
                                ind_s = text.index(name, c)
                                ind_e = ind_s + len(name)
                                break

                    suggs = suggest(name, safeeval_Default)
                    del temp[ind_s:ind_e]
                    temp.insert(ind_s, '<font color=red>'+name+'</font>')
                    error = ''.join(temp)
                    self.baloonShow('{0} {1} {2}'.format(self.invInput, error, suggs))

                except OverflowError as oe:
                    common._expr_tryassign = False
                    temp = oe.args[len(oe.args)-1]
                    error = translate('OverflowError', 'result too large')
                    if temp == 'Result too large':
                        self.baloonShow('{0} {1}'.format(
                                        translate('Balloon',
                                                  '<b>Overflow error:</b>'),
                                        error))
                    else:
                        self.baloonShow(translate('Balloon',
                                                  '<b>Overflow error:</b> {0}').format(temp))

                except ZeroDivisionError:
                    common._expr_tryassign = False
                    error = translate('Balloon',
                                      'cannot divide by zero!')
                    self.baloonShow(translate('Balloon',
                                              '<b>Zero division error:</b> {0}').format(error))
                except MathError as me:
                    common._expr_tryassign = False
                    temp = me.args[0]
                    self.baloonShow('{0} {1}'.format(
                                    '<b>Value error:</b>',
                                    temp))
                except ValueError as ve:
                    common._expr_tryassign = False
                    temp = ve.args[0]
                    error = translate('ValueError', 'math domain error')
                    if temp == 'math domain error':
                        self.baloonShow('{0} {1}'.format(
                                        translate('Balloon',
                                                  '<b>Value error:</b>'),
                                        error))
                    else:
                        self.baloonShow('{0} {1}'.format(
                                        translate('Balloon',
                                                  '<b>Value error:</b>'),
                                        temp))

                except Quickhelp as h:
                    common._expr_tryassign = False
                    func = h.funcname
                    args = h.argnames
                    self.baloonShow('<b>{0}({1})</b>, {2}'.format(func, args, h.text))

                except TypeError as te:
                    common._expr_tryassign = False
                    error = translate('TypeError',
                            'Numbers and variables cannot be used as a name'
                            ' of function - <font color=red>N</font><b>( )</b>,'
                            ' (<font color=red>N</font>)<b>( )</b>')
                    temp = te.args[0]
                    if temp in typeErrors:
                        self.baloonShow('{0} {1}'.format(
                                        translate('Balloon',
                                                  '<b>Function error:</b>'),
                                        error))
                    else:
                        if ':' in te.args[0]:
                            temp = te.args[0].split(':')[0]
                        self.baloonShow('{0} {1}'.format(
                                        translate('Balloon',
                                                  '<b>Function error:</b>'),
                                        temp))

    # Global EXCEPTION handler
    def exceptionHandler(self, type, value, tback):
        common._expr_tryassign = False
        log = [
                '\n',
                '{0}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                '-------------------\n',
                appname + ' v' + version,
                'Python v{0} & PyQt v{1} on {2} ({3}x{4})\n\n'.format(
                            python_version(),
                            QtCore.qVersion(),
                            _platform(),
                            self.screenW,
                            self.desktop.screenGeometry().height()),
            ]
        tb = traceback.format_exception(
                            type, value, tback)
        for i in range(len(tb)):
            if '\n' in tb[i]:
                tb[i].replace('\n', '\n    ')
            tb[i] = '    ' + tb[i]
        try:
            with open('error.log', 'a') as logfile:
                logfile.writelines(log + tb + ['\n\n'])

            error = translate('Balloon',
                                '<b>Unknown error occurred:</b> '
                                'Please, send log file (error.log) as a bug report')
            self.baloonShow(error)
        except:
            self.saveMessageBox(translate('MessageBox', 'Logging'),
                                translate('MessageBox',
                                            'Unable to save \'error.log\' file!\n'))


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.trayMenu = QtWidgets.QMenu()
        self.exitBtn = self.trayMenu.addAction(translate('Tray', 'Exit'), parent.exitApp)
        self.setContextMenu(self.trayMenu)
        self.activated.connect(parent.tray_activated)


class NumLockActivator(QtCore.QThread):

    def __init__(self, parent):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        self.setPriority(QtCore.QThread.LowestPriority)

        # watch for about 3 seconds and stop
        for x in range(10):
            sleep(0.2)
            if WinDLL("User32.dll").GetKeyState(0x90) == 0:
                common._virt_numlock_pressed = True
                winkeypress.PressKey(0x90)
                winkeypress.ReleaseKey(0x90)
                sleep(0.1)
                common._virt_numlock_pressed = False

    def stop(self):
        self.terminate()


class HotkeyListener(QtCore.QThread):

    hkPressed = QtCore.pyqtSignal()

    def __init__(self, parent, mod, key):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        self.mod = mod
        self.key = key

    def run(self):
        @GlobalHotKeys.register(GlobalHotKeys.kmap[PrefsDialog.keyList2[self.key].upper()],
                                GlobalHotKeys.kmap[PrefsDialog.keyList1[self.mod].upper()],
                                )   # reversed key order - VK+MOD
        def hotkeyExec():
            'Works with above decorator only'
            if common._virt_numlock_pressed:
                pass
            else:
                self.hkPressed.emit()

        try:
            GlobalHotKeys.listen()
        except KeyError:
            errorbaloon = BalloonWidget()
            QtWidgets.QMessageBox.information(self,
                translate('MessageBox', 'Global Shortcut'),
                translate('MessageBox',
                          'Unable to register Global Shortcut.<br /> '
                          'Try to restart the program.'))

    def stop(self):
        GlobalHotKeys.unreg()
        self.terminate()


if __name__ == '__main__':

    myappid = 'lmelikyan.app.sumcalc'

    if platform == 'win':   # >= Win7 -> major:6, minor:1
        if sys.getwindowsversion()[0] > 6 or \
                all((sys.getwindowsversion()[0] == 6,
                     sys.getwindowsversion()[1] > 0)):
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = SingleApplication(myappid, sys.argv)    # Inherits QtGui.QApplication()

    if app.isRunning():
        sys.exit(0)

    mainWindow = MainWindow()
    mainWindow.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint |
                              QtCore.Qt.WindowCloseButtonHint)

    mainWindow.tray.show()

    if common._start_minimized:
        mainWindow.hide()
        common._first_minimize = False
    else:
        mainWindow.show()

    if not QtCore.QFile.exists('settings.ini'):         # if it's the first start
        if platform == 'win' and mainWindow.key2 == 0:  # and NumLock is set as Global Shortcut
            QtWidgets.QMessageBox.information(mainWindow,
                                          translate('FirstStart', 'SUM First Start'),
                                          translate('FirstStart', firstStartMsg_NL))
        else:
            QtWidgets.QMessageBox.information(mainWindow,
                                          translate('FirstStart', 'SUM First Start'),
                                          translate('FirstStart', firstStartMsg))

    mainWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    mainWindow.moved_or_resized = False

    app.setActivationWindow(mainWindow)
    app.aboutToQuit().connect(mainWindow.exitApp)

    mainWindow.listView.scrollToBottom()
    mainWindow.lineedit.setFocus()

    # Setup exceptionhook
    sys.excepthook = mainWindow.exceptionHandler

    sys.exit(app.exec_())
