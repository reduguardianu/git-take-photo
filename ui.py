import os
import sys
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction
from threading import Thread
from main import GitPhotoRequestServer
from argparse import ArgumentParser
from loguru import logger


def runGui():
    qtApp = QApplication([])
    qtApp.setQuitOnLastWindowClosed(False)

    icon_path = str(Path(__file__).parent / "tray.png")
    icon = QIcon(icon_path)

    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    menu = QMenu()
    quitOption = QAction("Quit")
    quitOption.triggered.connect(qtApp.quit)
    menu.addAction(quitOption)

    tray.setContextMenu(menu)
    qtApp.exec()


if __name__ == "__main__":
    parser = ArgumentParser(description="git-take-photo GUI")
    parser.add_argument('--port', type=int, default=1234, help="Port on which local server will listen")
    parser.add_argument('--remote', required=False, help="Address of remote server")
    parser.add_argument('--webcam-priorities', required=False, nargs='+', default=[], help="Camera name priorities")
    parser.add_argument('--log-file', required=False, default=os.environ.get('GIT_PHOTO_LOG_FILE', 'git_photo.log'))
    parser.add_argument('--log-level', required=False, default="INFO")

    args = parser.parse_args()

    logger.remove()
    logger.add(args.log_file, level=args.log_level.upper(), rotation="10 MB", retention=5,
               format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")

    server = GitPhotoRequestServer(args.port, args.remote, args.webcam_priorities)
    logicThread = Thread(target=server.start, daemon=True)
    logicThread.start()
    runGui()
    server.shutdown()
    logicThread.join()
