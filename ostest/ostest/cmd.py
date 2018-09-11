import logging

from ostest.proxy import ServiceProxy, KeystoneTestAgent


logging.basicConfig(format='%(asctime)s %(levelname)-5s [%(name)s] %(message)s', level=logging.DEBUG)

keystone_test_agent = KeystoneTestAgent()
service_proxy = ServiceProxy()

try:
    service_proxy.start_server()
    keystone_test_agent.safely_alter_urls()
    while input() != 'quit':
        continue
except KeyboardInterrupt:
    pass
finally:
    keystone_test_agent.restore_urls()
    service_proxy.stop_server()