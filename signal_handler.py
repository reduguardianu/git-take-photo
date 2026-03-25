import signal
from loguru import logger

class SignalHandler:
    def __init__(self):
        self.shutdownRequest = False
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        logger.info("Shutting down. Bye!")
        self.shutdownRequest = True

    def canRun(self):
        return not self.shutdownRequest
