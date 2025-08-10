import os
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from threading import Thread
from main import GitPhotoRequestServer
import logging
import sys
from logging.handlers import RotatingFileHandler

def runGui():
    qtApp = QApplication([])
    qtApp.setQuitOnLastWindowClosed(False)
    icon = QIcon("tray.png")

    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    menu = QMenu()

    settingsOption = QAction("Settings")
    menu.addAction(settingsOption)
    quitOption = QAction("Quit")
    quitOption.triggered.connect(qtApp.quit)
    menu.addAction(quitOption)

    tray.setContextMenu(menu)
    qtApp.exec()



def logUnhandledException(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit(1)


if __name__ == "__main__":
    sys.excepthook = logUnhandledException
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[RotatingFileHandler(os.environ.get('GIT_PHOTO_LOG_FILE', 'git_photo.log'), backupCount=5, mode='w')],
    );
    server = GitPhotoRequestServer(1234, "http://nordvpn-huron6712.nord:8888", ["OBS", "Elgato"])
    logicThread = Thread(target=server.start, daemon=True)
    logicThread.start()
    runGui()
    server.shutdown()
    logicThread.join()
