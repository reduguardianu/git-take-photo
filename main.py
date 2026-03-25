#!/usr/bin/env python3
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from camera import takePhotoOnDevice
from signal_handler import SignalHandler
from functools import partial
from argparse import ArgumentParser
from loguru import logger
import sys


class GitPhotoRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, contextGetter, *args, **kwargs):
        context = contextGetter()
        self.connected = context['connected']
        self.cameraPriorities = context['cameraPriorities']
        self.photoServerAddress = context['address']
        super().__init__(*args, **kwargs)

    def do_GET(self):
        photo = self.getPhoto()
        if photo is None:
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-type", "image/png")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Disposition", "attachment")
        self.send_header("Content-Length", str(len(photo)))
        self.end_headers()
        self.wfile.write(photo)

    def getPhoto(self):
        if not self.connected:
            return takePhotoOnDevice(self.cameraPriorities)
        return self.getPhotoFromServer()

    def getPhotoFromServer(self):
        logger.info("Getting photo from remote server")
        reply = requests.get(self.photoServerAddress + "/getPhoto")
        logger.info("Photo downloaded from remote server")
        if reply.status_code == 200:
            return reply.content
        logger.warning("Remote server returned status {}", reply.status_code)
        return None


class GitPhotoRequestServer(HTTPServer):
    def __init__(self, localServerPort, photoServerAddress, cameraPriorities):
        self.cameraPriorities = cameraPriorities
        self.connected = False
        self.photoServerAddress = photoServerAddress
        self.signalHandler = SignalHandler()
        super().__init__(("127.0.0.1", localServerPort), partial(GitPhotoRequestHandler, self.getContext))

    def getContext(self):
        return {'connected': self.connected, 'cameraPriorities': self.cameraPriorities, 'address': self.photoServerAddress}

    def checkConnection(self):
        if self.photoServerAddress is None:
            return
        try:
            reply = requests.get(self.photoServerAddress + "/healthCheck", timeout=2)
            self.connected = reply.status_code == 200
        except Exception as e:
            logger.warning("Health check failed: {}", e)
            self.connected = False

    def getTime(self):
        return int(time.time())

    def runPeriodic(self):
        self.lastCheck = self.getTime()
        while self.signalHandler.canRun():
            if self.getTime() - self.lastCheck >= 20:
                self.lastCheck = self.getTime()
                self.checkConnection()
            time.sleep(1)
        self.shutdown()

    def shutdown(self):
        logger.info("Shutting down logic server")
        super().shutdown()
        self.signalHandler.shutdown(None, None)

    def start(self):
        logger.info("Starting up... listening on port {}", self.server_address[1])
        self.healthCheckThread = Thread(target=self.runPeriodic, daemon=True)
        self.healthCheckThread.start()
        self.serve_forever()


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Little utility, which goal is to serve photo taken via webcam or relay it to remote party if such party available",
        epilog="Have fun making something geeky ;)"
    )
    parser.add_argument('--port', type=int, required=True, help="Port on which local server will listen")
    parser.add_argument('--remote', required=False, help="Address of remote server, that will be asked for photo if connected. When this argument is omitted only local photos will be supported")
    parser.add_argument('--webcam-priorities', required=False, help="Names of camera which will take priority when taking local photo. If omitted first available device will be used", nargs='+', default=[])
    parser.add_argument('--log-file', required=False, help="Path to log file. If not specified, logging will be printed to stdout", default=None)
    parser.add_argument('--log-level', required=False, help="Logging level. Default is INFO", default="INFO")

    args = parser.parse_args()

    logger.remove()
    if args.log_file:
        logger.add(args.log_file, level=args.log_level.upper(), rotation="10 MB", retention=5,
                   format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
    else:
        logger.add(sys.stdout, level=args.log_level.upper(),
                   format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")

    logger.catch(sys.exit)(lambda: None)

    server = GitPhotoRequestServer(args.port, args.remote, args.webcam_priorities)
    server.start()
