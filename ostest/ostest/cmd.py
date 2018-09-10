import logging

from ostest import proxy

logging.basicConfig(format='%(asctime)s %(levelname)-5s %(message)s', level=logging.DEBUG)

log = logging.getLogger("cmd")
myProxy = proxy.ApiProxy()

try:
    myProxy.alter_original_endpoints()
    myProxy.start()
    while input() != "quit":
        continue
finally:
    myProxy.stop()
    myProxy.restore_original_endpoints()