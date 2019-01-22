import signal
import os
import time
import threading
import logging

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = '%(levelname) -6s %(asctime)s %(threadName) -15s %(funcName) -15s: %(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


LOGGER.info('%r', signal.SIGUSR1)