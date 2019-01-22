import signal
import os
import time
import threading
import logging

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = '%(levelname) -6s %(asctime)s %(threadName) -15s %(funcName) -15s: %(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


LOGGER.info('My PID is %i', os.getpid())

start_time = time.time()
while True:
    time.sleep(3)
    LOGGER.info('Updating time %is', time.time() - start_time)
