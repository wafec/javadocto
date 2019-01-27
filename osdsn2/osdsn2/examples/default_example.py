import logging
import psutil
import time

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = '%(message)s'

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


try:
    while True:
        time.sleep(1)
        logging.debug('CPU=%s, MEM=%s, SWAP=%s', psutil.cpu_percent(),
                      psutil.virtual_memory().percent, psutil.swap_memory().percent)
except KeyboardInterrupt:
    pass
