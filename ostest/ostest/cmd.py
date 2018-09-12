import logging

from ostest.proxy import ServiceProxy, KeystoneOSTestAgent, RabbitTestAgent, QueueProxy


logging.basicConfig(format='%(asctime)s %(levelname)-5s [%(name)s] %(message)s', level=logging.DEBUG)

keystone_test_agent = KeystoneOSTestAgent()
service_proxy = ServiceProxy()
rabbit_test_agent = RabbitTestAgent()
queue_proxy = QueueProxy()

try:
    service_proxy.start()
    keystone_test_agent.safely_alter_urls()

    rabbit_test_agent.restore_bindings()
    rabbit_test_agent.alter_bindings()
    queue_proxy.start()

    while input() != 'quit':
        continue
except KeyboardInterrupt:
    pass
finally:
    keystone_test_agent.restore_urls()
    service_proxy.stop()

    rabbit_test_agent.restore_bindings()
    queue_proxy.stop()