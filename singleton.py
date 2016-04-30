# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


from PyQt5 import QtCore, QtWidgets
from PyQt5.QtNetwork import QLocalSocket, QLocalServer


class SingleApplication(QtWidgets.QApplication):
    '''
    Inheriting from QApplication, executing main App instead.
    Watching whether the app is already running.
    If so, quit befor execution.
    '''
    messageReceived = QtCore.pyqtSignal(str)

    def __init__(self, id, *argv):

        super(SingleApplication, self).__init__(*argv)
        self._id = id
        self._activationWindow = None
        self._activateOnMessage = False

        # Check if another instance is running?
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._id)
        self._isRunning = self._outSocket.waitForConnected()

        if self._isRunning:
            self._outStream = QtCore.QTextStream(self._outSocket)
            self._outStream.setCodec('UTF-8')
        else:
            self._outSocket = None
            self._outStream = None
            self._inSocket = None
            self._inStream = None
            self._server = QLocalServer()
            self._server.removeServer(self._id)  # if existing after crash-exit
            self._server.listen(self._id)
            self._server.newConnection.connect(self._onNewConnection)

    def isRunning(self):
        return self._isRunning

    def id(self):
        return self._id

    def activationWindow(self):
        return self._activationWindow

    def setActivationWindow(self, activationWindow, activateOnMessage=True):
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self):
        if not self._activationWindow:
            return
        self._activationWindow.setWindowState(
            self._activationWindow.windowState() & ~QtCore.Qt.WindowMinimized)
        self._activationWindow.show()
        self._activationWindow.activateWindow()

    def sendMessage(self, msg):
        if not self._outStream:
            return False
        self._outStream << msg << '\n'
        self._outStream.flush()
        return self._outSocket.waitForBytesWritten()

    def _onNewConnection(self):
        if self._inSocket:
            self._inSocket.readyRead.disconnect(self._onReadyRead)
        self._inSocket = self._server.nextPendingConnection()
        if not self._inSocket:
            return
        self._inStream = QtCore.QTextStream(self._inSocket)
        self._inStream.setCodec('UTF-8')
        self._inSocket.readyRead.connect(self._onReadyRead)
        if self._activateOnMessage:
            self.activateWindow()

    def _onReadyRead(self):
        while True:
            msg = self._inStream.readLine()
            if not msg:
                break
            self.messageReceived.emit(msg)
