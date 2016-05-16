# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


from math import isfinite
from PyQt5 import QtCore, QtGui, QtWidgets

import common
from mathfuncs import safeeval_dict


historyMax = 250    # Maximum expressions in history

cvNameMax = 8      # Maximum length of new assignement's name
cvValueMax = 32     # Maximum length of new assignement's value

# Pinned Constants, editing available only in source code below
constants = {
                'e' : 2.718281828459045,
                'pi': 3.141592653589793,
            }

# Custom constants and variables, editing available by dialogs
cstmConstVars = {}

translate = QtWidgets.QApplication.translate


class ListView(QtWidgets.QListView):
    '''
    Modified QListView with overloaded focusInEvent(),
    using in ConstDialog class.
    '''
    getFocus = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ListView, self).__init__(parent)

    def focusInEvent(self, event):
        if self.hasFocus():
            self.getFocus.emit()

        super(ListView, self).focusInEvent(event)


class ConstDialog(QtWidgets.QDialog):
    '''
    Constants and Variables dialog DESIGN
    '''
    def __init__(self, parent=None):
        super(ConstDialog, self).__init__(parent)

        self.constvarFile = 'constvars.txt'

        self.setWindowFlags(QtCore.Qt.WindowTitleHint)
        self.app_icon = QtGui.QIcon()   # set in main module
        self.setWindowTitle(translate('ConstVarDialog', 'Constants and Variables'))

        self.inputLine = QtWidgets.QLineEdit()
        self.listView = ListView()
        self.setMinimumWidth(300)
        self.constvarModel = QtGui.QStandardItemModel(self.listView)
        self.constvarModel.setColumnCount(1)
        self.statBar =QtWidgets.QLabel(translate('ConstVarDialog',
                                              'Add new constant or variable.<br />Pattern: '
                                              '<b>name</b> ({0}) = <b>value</b> ({1})').format(cvNameMax, cvValueMax))
        self.statBar.setMinimumHeight(self.statBar.sizeHint().height())
        self.infoNote = QtWidgets.QLabel(translate('ConstVarDialog',
                                               'Temporary (unchecked) variable assignment<br />'
                                               'is available by the main calculation field.'))
        self.warnNote = QtWidgets.QLabel(translate('ConstVarDialog',
                                               'Note: All unchecked fields '
                                               'get lost on Exit.'))
        self.infoNote.setAlignment(QtCore.Qt.AlignRight)
        self.warnNote.setAlignment(QtCore.Qt.AlignRight)
        self.listView.setModel(self.constvarModel)
        self.listView.setAlternatingRowColors(True)
        self.listView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Close,
            QtCore.Qt.Horizontal)

        self.listView.getFocus.connect(self.firstSel)
        self.listView.customContextMenuRequested.connect(self.listContextMenu)
        self.inputLine.returnPressed.connect(self.getInput)
        self.inputLine.textChanged.connect(self.statTurnBack)
        self.buttons.clicked.connect(self.close)

        constLayout = QtWidgets.QVBoxLayout()
        listLayout = QtWidgets.QVBoxLayout()
        noteLayout = QtWidgets.QVBoxLayout()
        listLayout.addWidget(self.listView)
        listLayout.addWidget(self.statBar)
        listLayout.setContentsMargins(0, 0, 0, 18)
        listLayout.setSpacing(3)
        noteLayout.addWidget(self.warnNote)
        noteLayout.addWidget(self.infoNote)
        noteLayout.setSpacing(6)
        noteLayout.setContentsMargins(0, 0, 0, 12)

        constLayout.addWidget(self.inputLine)
        constLayout.addItem(listLayout)
        constLayout.addItem(noteLayout)
        constLayout.addWidget(self.buttons)

        self.setLayout(constLayout)

        # Load Constants on init
        for c in sorted(constants):
            safeeval_dict[c] = constants[c]
            it = QtGui.QStandardItem('{0}\t=  {1}'.format(c, constants[c]))
            it.setEditable(False)
            it.setEnabled(False)
            it.setCheckable(True)
            it.setCheckState(2)
            self.constvarModel.appendRow(it)


        self.loadConstVars()

        # END __init__

    def closeEvent(self, e):
        self.inputLine.clear()
        self.listView.selectionModel().clear()
        self.saveConstVars()
        super(ConstDialog, self).closeEvent(e)

    def firstSel(self):
        if self.listView.currentIndex().row() > 0:
            pass
        else:
            if self.constvarModel.rowCount() > len(constants):
                index = self.constvarModel.index(len(constants), 0)
                self.listView.selectionModel().select(
                    index,
                    QtCore.QItemSelectionModel.ClearAndSelect)

    def listContextMenu(self, pos):
        lstContMenu = QtWidgets.QMenu()
        curIndex = self.listView.indexAt(pos).row()
        if curIndex >= 0:
            allowDel = self.constvarModel.item(curIndex).isEnabled()
            if allowDel:
                if self.constvarModel.item(curIndex).checkState() == 0:
                    lstContMenu.addAction(translate('ConstVarCtx',
                                                    'Check'),
                                          self.checkLine, 'Space')
                elif self.constvarModel.item(curIndex).checkState() == 2:
                    lstContMenu.addAction(translate('ConstVarCtx',
                                                    'Uncheck'),
                                          self.uncheckLine, 'Space')
                lstContMenu.addSeparator()
                lstContMenu.addAction(translate('ConstVarCtx',
                                                'Delete'),
                                      self.delConstVar, 'Del')

                lstContMenu.exec_(self.listView.viewport().mapToGlobal(pos))
        else:
            self.listView.selectionModel().clear()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Delete and\
                self.listView.selectionModel().hasSelection():

            self.delConstVar()

        elif e.key() == QtCore.Qt.Key_Return or\
                e.key() == QtCore.Qt.Key_Enter:

            if self.inputLine.hasFocus():
                    pass
            else:
                return super(ConstDialog, self).keyPressEvent(e)

        elif e.key() == QtCore.Qt.Key_Escape:
            if self.inputLine.text():
                if self.inputLine.hasFocus():
                    self.inputLine.clear()
                else:
                    self.inputLine.setFocus()
            else:
                self.close()    # call closeEvent to repeat closing procedure
                return super(ConstDialog, self).keyPressEvent(e)
        else:
            return super(ConstDialog, self).keyPressEvent(e)

    def delConstVar(self):
        if self.listView.currentIndex().row() >= len(constants):
            self.constvarModel.removeRow(self.listView.currentIndex().row())
            line = self.constvarModel.data(self.listView.currentIndex())
            if line:
                name = line.split('=')[0].strip()
                del safeeval_dict[name]
                del cstmConstVars[name]

    def statTurnBack(self):
        self.statBar.setText(translate('ConstVarDialog',
                                        'Add new constant or variable.<br />Pattern: '
                                        '<b>name</b> ({0}) = <b>value</b> ({1})').format(cvNameMax, cvValueMax))

    def checkLine(self):
        self.constvarModel.item(self.listView.currentIndex().row()).setCheckState(2)

    def uncheckLine(self):
        self.constvarModel.item(self.listView.currentIndex().row()).setCheckState(0)

    @classmethod
    def checkConstVar(cls, item):

        radd = {'0b': [2, 'bin'],
                '0o': [8, 'oct'],
                '0x': [16, 'hex']}

        def turnNumber(strValue):
            try:
                f = float(strValue)
                if not isfinite(f):
                    raise ValueError('Result too large')
                elif f == int(f) and 'e' not in str(f):
                    return str(int(f))
                elif 'e' in str(f):
                    return str(f)
                else:
                    return str(round(f, 15))
            except ValueError:
                # check for BinOctHex
                for x in radd:
                    if x in strValue.lower():
                        try:
                            boh = int(strValue, radd[x][0])
                            return eval('{0}({1})'.format(radd[x][1], boh))
                        except ValueError:
                            return ''
                return ''

        if item.count('=') != 1:
            return ()
        else:
            left = item.split('=')[0].strip()
            right = item.split('=')[1].strip()
            if left.isidentifier():
                if turnNumber(right):
                    if len(left) > cvNameMax or len(right) > cvValueMax:
                        return (1, 0)
                    return (left, turnNumber(right))    # 'right' is a number
                else:
                    common._expr_tryassign = True
                    return (left, right)                # 'right' may be anything
            return ()

    def getInput(self):
        if not self.inputLine.text():
            self.close()
        else:
            self.addConstVar(self.inputLine.text())

    def addConstVar(self, text):

        assignInc = translate('ConstVarDialog',
                              '<b>Assignement is incorrect!</b>')
        invName = translate('ConstVarDialog',
                            '<b>Invalid name!</b>')

        checkedLine = ConstDialog.checkConstVar(text)
        if checkedLine:
            if checkedLine == (1, 0):
                self.statBar.setText(translate('ConstVarDialog',
                    '{0}<br />name or value length is exceeded ({1}, {2}).').format(
                        assignInc, cvNameMax, cvValueMax))
            elif common._expr_tryassign:
                self.statBar.setText(translate('ConstVarDialog',
                    '{0}<br />Value must be a number (and not an expression).').format(assignInc))
                common._expr_tryassign = False
            elif checkedLine[0] in cstmConstVars:
                for i in range(self.constvarModel.rowCount()):
                    n = self.constvarModel.data(
                        self.constvarModel.index(i, 0)).split('=')[0].strip()
                    if checkedLine[0] == n:
                        if self.constvarModel.item(i).checkState() == 0:
                            # Update existing temporary variable
                            self.constvarModel.item(i).setText('{0}\t=  {1}'.format(*checkedLine))
                            self.listView.scrollTo(self.constvarModel.index(i, 0))
                            self.inputLine.clear()
                        else:
                            self.statBar.setText(translate('ConstVarDialog',
                                '{0}<br />Name <b>{1}</b> is non-temporary.').format(invName, checkedLine[0]))
                        break

            elif checkedLine[0] in safeeval_dict or checkedLine[0] in constants:
                self.statBar.setText(translate('ConstVarDialog',
                    '{0}<br />Name <b>{1}</b> is reserved.').format(invName, checkedLine[0]))
            else:
                cstmConstVars[checkedLine[0]] = eval(checkedLine[1])
                safeeval_dict[checkedLine[0]] = eval(checkedLine[1])
                item = QtGui.QStandardItem('{0}\t=  {1}'.format(*checkedLine))
                item.setEditable(False)
                item.setCheckable(True)
                item.setCheckState(2)   # Checked by default
                self.constvarModel.appendRow(item)
                self.listView.scrollToBottom()
                self.inputLine.clear()
        else:
            self.statBar.setText(translate('ConstVarDialog',
                '{0}<br />See Help for lexical limitations.').format(assignInc))

    def loadConstVars(self):
        f = QtCore.QFile(self.constvarFile)
        if f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            stream = QtCore.QTextStream(f)
            stream.setCodec('UTF-8')
            line = stream.readLine()
            while line:
                checkedLine = ConstDialog.checkConstVar(line)
                if checkedLine:
                    if not checkedLine[0] in cstmConstVars and\
                            not checkedLine[0] in constants and\
                            not checkedLine[0] in safeeval_dict:
                        cstmConstVars[checkedLine[0]] = eval(checkedLine[1])
                        safeeval_dict[checkedLine[0]] = eval(checkedLine[1])
                        item = QtGui.QStandardItem('{0}\t=  {1}'.format(*checkedLine))
                        item.setEditable(False)
                        item.setCheckable(True)
                        item.setCheckState(2)
                        self.constvarModel.appendRow(item)
                line = stream.readLine()
            f.close()
        else:
            pass

    def saveConstVars(self):
        f = QtCore.QFile(self.constvarFile)
        line = QtCore.QByteArray()
        if f.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            for row in range(self.constvarModel.rowCount()):
                if self.constvarModel.item(row, 0).isEnabled() and\
                        self.constvarModel.item(row, 0).checkState() == 2:
                    line.append((self.constvarModel.data(
                        self.constvarModel.index(row, 0)) + '\n').encode('UTF-8'))
                else:
                    continue
            f.write(line)
            f.close()
        else:
            self.saveMessageBox(translate('MessageBox',
                                          'Constants and Variables'),
                                translate('MessageBox',
                                          '{0} Unable to save \'{1}\' file!\n').format(
                                                f.errorString(),
                                                self.constvarFile))


class PrefsDialog(QtWidgets.QDialog):
    '''
    Preferences window DESIGN
    '''
    languages = {
                    # English
                    'English': 'en_US',
                    'Russian': 'ru_RU',
                    # Russian
                    'Английский': 'en_US',
                    'Русский': 'ru_RU',
                }

    keyList1 = ['', 'Ctrl']

    keyList2 = ['NumLock']  # Loop below appends F2-F12
    for d in range(2, 13):
                keyList2.append('F{0}'.format(str(d).upper()))

    def __init__(self, parent=None):
        super(PrefsDialog, self).__init__(parent)

        self.setWindowFlags(QtCore.Qt.WindowTitleHint)
        self.setWindowTitle(translate('Prefs', 'Preferences'))

        uiGroup = QtWidgets.QGroupBox(translate('Prefs', 'User Interface'))
        uiLayout = QtWidgets.QHBoxLayout()
        # -
        uiLangLayout = QtWidgets.QHBoxLayout()
        uiLangLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.uiLangSelect = QtWidgets.QComboBox()
        self.uiLangSelect.addItems([
                            translate('LangList', 'English'),
                            translate('LangList', 'Russian')])
        self.uiLangSelect.setMinimumWidth(75)
        self.uiLangSelect.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.uiLangSelect.setEditable(False)
        self.uiLangLabel = QtWidgets.QLabel(translate('Prefs', 'Language: '))
        uiLangLayout.addWidget(self.uiLangLabel)
        uiLangLayout.addWidget(self.uiLangSelect)
        # -
        uiLeftLayout = QtWidgets.QVBoxLayout()
        uiLeftLayout.setAlignment(QtCore.Qt.AlignTop)
        uiLeftLayout.addItem(uiLangLayout)
        # -
        uiResLayout = QtWidgets.QVBoxLayout()
        uiResLayout.setAlignment(QtCore.Qt.AlignTop)
        resToolTip = translate('Prefs',
            'Double is recomended if screen resolution is UltraHD or higher.')
        self.uiResSelect = QtWidgets.QComboBox()
        self.uiResSelect.addItems([translate('Prefs', 'Native'),
                                   translate('Prefs', 'Double')])
        self.uiResSelect.setMinimumWidth(75)
        self.uiResSelect.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.uiResSelect.setEditable(False)
        self.uiResSelect.setToolTip(resToolTip)
        self.uiResLabel = QtWidgets.QLabel(translate('Prefs', 'Resolution: '))
        self.uiResLabel.setToolTip(resToolTip)
        uiResSelectLayout = QtWidgets.QHBoxLayout()
        uiResSelectLayout.setContentsMargins(0, 0, 0, 7)
        uiResSelectLayout.setAlignment(QtCore.Qt.AlignRight)
        uiResSelectLayout.addWidget(self.uiResLabel)
        uiResSelectLayout.addWidget(self.uiResSelect)
        uiResLayout.addItem(uiResSelectLayout)
        # -
        uiLayout.addItem(uiLeftLayout)
        uiLayout.addItem(uiResLayout)
        uiGroup.setLayout(uiLayout)

        mathGroup = QtWidgets.QGroupBox(translate('Prefs', 'Calculations'))
        mathLayout = QtWidgets.QHBoxLayout()
        # -
        mathLeftLayout = QtWidgets.QVBoxLayout()
        mathLeftLayout.setAlignment(QtCore.Qt.AlignTop)
        self.constButton = QtWidgets.QPushButton(translate('Prefs', 'C&onstants...'))
        self.constButton.setMaximumWidth(self.constButton.sizeHint().width() + 20)
        self.calcScient = QtWidgets.QCheckBox(translate('Prefs',
                                                    'Large integer result in &Scientific Notation'))
        self.calcScient.setToolTip('<p style="white-space:pre">42<sup>42</sup>'
                                   ' = 1.5013093754529656e+68</p>')
        mathLeftLayout.setSpacing(6)
        mathLeftLayout.addWidget(self.calcScient)
        mathLeftLayout.addWidget(self.constButton)
        # -
        angLayout = QtWidgets.QVBoxLayout()
        angLayout.setContentsMargins(32, 0, 0, 0)
        angLayout.setSpacing(6)
        angLayout.setAlignment(QtCore.Qt.AlignTop)
        self.angDegrees = QtWidgets.QRadioButton(translate('Prefs', '&Degrees'))
        self.angRadians = QtWidgets.QRadioButton(translate('Prefs', '&Radians'))
        angToolTip = translate('Prefs',
                               'Angles in trigonometry'
                               ' (pay attantion to actual angle indication in main Titlebar)')
        self.angDegrees.setToolTip(angToolTip)
        self.angRadians.setToolTip(angToolTip)
        angLayout.addWidget(self.angDegrees)
        angLayout.addWidget(self.angRadians)
        # -
        mathLayout.addItem(mathLeftLayout)
        mathLayout.addItem(angLayout)
        mathGroup.setLayout(mathLayout)

        hstGroup = QtWidgets.QGroupBox(translate('Prefs', 'History'))
        hstLayout = QtWidgets.QVBoxLayout()
        self.hstReformat = QtWidgets.QCheckBox(translate('Prefs',
                                                     'Re&format expression in History'))
        self.hstReformat.setToolTip('42+sin(1/.4-3)  >>>  42 + sin(1/0.4 - 3)')
        self.hstCount = QtWidgets.QSpinBox()
        self.hstCount.setAlignment(QtCore.Qt.AlignRight)
        self.hstCount.setRange(0, 1000)
        self.hstCount.setSingleStep(10)
        self.hstCount.stepBy(10)
        self.hstCount.setToolTip(translate('Prefs', 'max: {0}').format(historyMax))
        self.hstCount.valueChanged.connect(self.hstCountChanged)
        self.hstCount.editingFinished.connect(self.hstCountSet)
        self.hstCountLabel = QtWidgets.QLabel(translate('Prefs',
                                                    '  expressions in History'))
        countLayout = QtWidgets.QHBoxLayout()
        countLayout.setContentsMargins(0, 2, 0, 2)
        countLayout.setAlignment(QtCore.Qt.AlignLeft)
        countLayout.addWidget(self.hstCount)
        countLayout.addWidget(self.hstCountLabel)
        self.hstAdd = QtWidgets.QCheckBox(translate('Prefs', 'Add to &History'))
        self.hstAdd.stateChanged.connect(self.hstAddChange)
        self.hstAutoClear = QtWidgets.QCheckBox(translate('Prefs',
                                                      'Clear History on &Exit'))
        self.hstClear = QtWidgets.QPushButton(translate('Prefs', '&Clear History'))
        self.hstClear.setMaximumWidth(self.hstClear.sizeHint().width() + 20)
        hstLayout.setSpacing(6)
        hstLayout.addWidget(self.hstReformat)
        hstLayout.addItem(countLayout)
        hstLayout.addWidget(self.hstAdd)
        hstLayout.addWidget(self.hstAutoClear)
        hstLayout.addWidget(self.hstClear)
        hstGroup.setLayout(hstLayout)

        self.globLabel = QtWidgets.QLabel(translate('Prefs', ' Global Shortcut Key:  '))
        self.globKey1 = QtWidgets.QComboBox()
        self.globKey1.addItems(self.keyList1)
        self.globKey1.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.globKey1.currentIndexChanged[int].connect(self.key1ComboChange)
        self.globKey2 = QtWidgets.QComboBox()
        self.globKey2.addItems(self.keyList2)
        self.globKey2.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.globKey2.currentIndexChanged[int].connect(self.key2ComboChange)
        self.globPlus = QtWidgets.QLabel('+')
        self.globPlus.setMinimumWidth(18)
        self.globPlus.setAlignment(QtCore.Qt.AlignCenter)
        if self.globKey1.currentIndex() == 0:
            self.globPlus.setText('-')
        self.globNote = QtWidgets.QLabel(translate('Prefs',
                                               'Note: If NumLock key is chosen,\n'
                                               'NumLock state will be always On.'))
        self.globNote.setAlignment(QtCore.Qt.AlignRight)
        self.globNote.setWordWrap(True)

        self.restBtn = QtWidgets.QPushButton(translate('Prefs', 'Reset All'))
        self.restBtn.setToolTip(translate('Prefs',
                                          'Reset all preferences and UI settings (size, position, etc.).'))
        self.restBtn.setMinimumWidth(self.restBtn.sizeHint().width() + 20)

        self.btmLine = QtWidgets.QFrame()
        self.btmLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.btmLine.setFrameShadow(QtWidgets.QFrame.Plain)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal)

        self.startMinimized = QtWidgets.QCheckBox(translate('Prefs', 'Start &Minimized'))

        startMinLayout = QtWidgets.QHBoxLayout()
        startMinLayout.setAlignment(QtCore.Qt.AlignLeft)
        startMinLayout.setContentsMargins(hstLayout.contentsMargins().left(), 8, 0, 6)
        startMinLayout.addWidget(self.startMinimized)

        globKeyLayout = QtWidgets.QHBoxLayout()
        globKeyLayout.setAlignment(QtCore.Qt.AlignRight)
        globKeyLayout.addWidget(self.globLabel)
        globKeyLayout.addWidget(self.globKey1)
        globKeyLayout.addWidget(self.globPlus)
        globKeyLayout.addWidget(self.globKey2)
        globLayout = QtWidgets.QVBoxLayout()
        globLayout.addItem(globKeyLayout)
        globLayout.addWidget(self.globNote)
        globLayout.setContentsMargins(0, 6, 0, 6)
        globLayout.setSpacing(6)

        resetLayout = QtWidgets.QVBoxLayout()
        resetLayout.setAlignment(QtCore.Qt.AlignVCenter)
        resetLayout.setContentsMargins(0, 6, 0, 12)
        resetLayout.addWidget(self.restBtn, alignment=QtCore.Qt.AlignRight)
        resetLayout.setSpacing(6)

        btnLayout = QtWidgets.QHBoxLayout()
        btnLayout.addWidget(self.buttons)
        btnLayout.setContentsMargins(0, 6, 0, 2)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(uiGroup)
        mainLayout.addWidget(mathGroup)
        mainLayout.addWidget(hstGroup)
        mainLayout.addItem(startMinLayout)
        mainLayout.addItem(globLayout)
        mainLayout.addItem(resetLayout)
        mainLayout.addWidget(self.btmLine)
        mainLayout.addItem(btnLayout)
        self.setLayout(mainLayout)

    def key2ComboChange(self):
        if self.globKey2.currentIndex() == 0:
            self.globKey1.setCurrentIndex(0)
            self.globPlus.setText('-')
        else:
            self.globKey1.setCurrentIndex(1)
            self.globPlus.setText('+')

    def key1ComboChange(self):
        if self.globKey1.currentIndex() == 0:
            if self.globKey2.currentIndex() == 0:
                pass
            else:
                self.globKey2.setCurrentIndex(0)
                self.globPlus.setText('-')
        else:
            if self.globKey2.currentIndex() == 0:
                self.globKey2.setCurrentIndex(1)
                self.globPlus.setText('+')
            else:
                pass

    def hstCountChanged(self):
        if self.hstCount.value() > historyMax:
            self.hstCount.setValue(historyMax)

    def hstCountSet(self):
        if self.hstCount.value() == 0:
            self.hstCount.setDisabled(True)
            self.hstAdd.setChecked(False)

    def hstAddChange(self):
        if self.hstAdd.isChecked():
            if self.hstCount.value() == 0:
                self.hstCount.setValue(1)
            self.hstCount.setEnabled(True)
        elif not self.hstAdd.isChecked():
            self.hstCount.setDisabled(True)
