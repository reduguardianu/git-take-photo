#!/usr/bin/env python3
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from camera import takePhotoOnDevice
from signal_handler import SignalHandler
from functools import partial
from argparse import ArgumentParser

class GitPhotoRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, contextGetter, *args, **kwargs):
        context = contextGetter()
        self.connected = context['connected']
        self.cameraPriorities = context['cameraPriorities']
        self.photoServerAddress = context['address']
        super().__init__(*args, **kwargs)

    def do_GET(self):
        photo = self.getPhoto()
        self.send_response(200)
        self.send_header("Content-type", "image/png")
        self.send_header("Accept-Ranges","bytes")
        self.send_header("Content-Disposition","attachment")
        self.send_header("Content-Length", str(len(photo)))
        self.end_headers()
        self.wfile.write(photo)

    def getPhoto(self):
        if not self.connected:
            return takePhotoOnDevice(self.cameraPriorities)
        return self.getPhotoFromServer()

    def getPhotoFromServer(self):
        reply = requests.get(self.photoServerAddress + "/getPhoto")
        if reply.status_code == 200:
            return reply.content
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
            reply = requests.get(self.photoServerAddress + "/healthCheck")
            self.connected = reply.status_code == 200
            print(self.connected)
        except Exception as e:
            print(e)
            self.connected = False

    def getTime(self):
        return int(time.time())

    def runPeriodic(self):
        self.startTime = self.getTime()

        while self.signalHandler.canRun():
            if (self.getTime() - self.startTime) % 60 == 0:
                self.checkConnection()
            time.sleep(1)
        self.shutdown()

    def start(self):
        self.healthCheckThread = Thread(target=self.runPeriodic, daemon=True)
        self.healthCheckThread.start()
        self.serve_forever()

if __name__ == "__main__":
    parser = ArgumentParser(description="Little utility, which goal is to serve photo taken via webcam or relay it to remote party if such party available", epilog="Have fun making somethig geeky ;)")

    parser.add_argument('--port', type=int, required=True, help="Port on which local server will listen")
    parser.add_argument('--remote', required=False, help="Address of remote server, that will be asked for photo if connected. When this argument is ommited only local photos will be supported")
    parser.add_argument('--webcam-priorities', required=False, help="Names of camera which will take priority when taking local photo. If ommited first available device will be used", nargs='+', default=[])

    arguments = parser.parse_args()
    print(arguments)

    server = GitPhotoRequestServer(arguments.port, arguments.remote, arguments.webcam_priorities)
    server.start()
