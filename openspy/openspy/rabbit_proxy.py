import pika
import logging
from threading import Thread
import json
from munch import munchify
from openspy import injection


class RabbitBase:
    FAKE_IN_PREFIX = "FAKEIN_"
    FAKE_OUT_PREFIX = "FAKEOUT_"

    def __init__(self, conf):
        self.CONF = conf

    def get_channel(self):
        credentials = pika.PlainCredentials(self.CONF.rabbit.username, self.CONF.rabbit.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            self.CONF.rabbit.host,
            self.CONF.rabbit.port,
            self.CONF.rabbit.vhost,
            credentials
        ))
        return connection.channel(), connection


class RabbitFaker(RabbitBase):
    def __init__(self, conf):
        super(RabbitFaker, self).__init__(conf)

    def alter_bindings(self):
        cha, _ = self.get_channel()
        for queue_binding in self.CONF.rabbit.queue.bindings:
            cha.queue_unbind(
                queue=queue_binding.queue_name,
                exchange=queue_binding.exchange_name,
                routing_key=queue_binding.routing_key
            )
            r = cha.queue_declare(
                queue=self.FAKE_IN_PREFIX + queue_binding.queue_name
            )
            cha.queue_bind(
                queue=r.method.queue,
                exchange=queue_binding.exchange_name,
                routing_key=queue_binding.routing_key
            )
            cha.queue_bind(
                queue=queue_binding.queue_name,
                exchange=queue_binding.exchange_name,
                routing_key=self.FAKE_OUT_PREFIX + queue_binding.routing_key
            )

    def restore_bindings(self):
        cha, _ = self.get_channel()
        for queue_binding in self.CONF.rabbit.queue.bindings:
            cha.queue_unbind(
                queue=self.FAKE_IN_PREFIX + queue_binding.queue_name,
                exchange=queue_binding.exchange_name,
                routing_key=queue_binding.routing_key
            )
            cha.queue_unbind(
                queue=queue_binding.queue_name,
                exchange=queue_binding.exchange_name,
                routing_key=self.FAKE_OUT_PREFIX + queue_binding.routing_key
            )
            cha.queue_delete(
                queue=self.FAKE_IN_PREFIX + queue_binding.queue_name
            )
            cha.queue_bind(
                queue=queue_binding.queue_name,
                exchange=queue_binding.exchange_name,
                routing_key=queue_binding.routing_key
            )


class RabbitProxy(RabbitBase):
    LOG = logging.getLogger("RabbitProxy")
    default_injector = injection.GenericInjector()

    def __init__(self, conf):
        super(RabbitProxy, self).__init__(conf)
        self._mainthread = None
        self._clithreads = []
        self._clichannels = []
        self._queue_bindings = []

    def _start(self):
        self._initialize(self.CONF.rabbit.queue.bindings)

    def _initialize(self, queue_bindings):
        for queue_binding in queue_bindings:
            cha, _ = self.get_channel()
            self._clichannels.append(cha)
            t = Thread(target=self._start_cli, args=[cha, queue_binding])
            self._clithreads.append(t)
            self._queue_bindings.append(queue_binding)
            t.daemon = True
            t.start()

    def _start_cli(self, cha, queue_binding):
        cha.basic_consume(self._callback, queue=self.FAKE_IN_PREFIX + queue_binding.queue_name, no_ack=True)
        cha.start_consuming()

    def _get_ch_index(self, ch):
        for i in range(0, len(self._clichannels)):
            if self._clichannels[i] == ch:
                return i
        return -1

    def _make_a_bind_if_needed(self, oslo_message):
        if "_reply_q" in oslo_message and oslo_message["_reply_q"]:
            self.LOG.debug(f"Making a reply to {oslo_message['_reply_q']}")
            direct_name = oslo_message["_reply_q"]
            cha, _ = self.get_channel()

            cha.queue_declare(
                queue=self.FAKE_IN_PREFIX + direct_name
            )
            cha.exchange_declare(
                exchange=self.FAKE_IN_PREFIX + direct_name
            )

            self.LOG.debug(f"Queue and exchange names are {self.FAKE_IN_PREFIX + direct_name}")

            cha.queue_bind(
                exchange=self.FAKE_IN_PREFIX + direct_name,
                queue=self.FAKE_IN_PREFIX + direct_name,
                routing_key=self.FAKE_IN_PREFIX + direct_name
            )

            self._initialize([
                munchify({
                    "exchange_name": direct_name,
                    "queue_name": direct_name,
                    "routing_key": direct_name
                })
            ])
            oslo_message["_reply_q"] = self.FAKE_IN_PREFIX + direct_name

        return json.dumps(oslo_message)

    def _callback(self, ch, method, properties, body):
        self.LOG.debug(f'[x] {method.routing_key}')
        i = self._get_ch_index(ch)
        if i >= 0:
            queue_binding = self._queue_bindings[i]
            self.LOG.warn(f'[x] {self.FAKE_OUT_PREFIX + queue_binding.routing_key}')
            cliout, connout = self.get_channel()

            message = json.loads(body)
            oslo_message = self._make_a_bind_if_needed(json.loads(message["oslo.message"]))
            message["oslo.message"] = oslo_message
            body = json.dumps(message)

            # BEGIN CALL
            routing_key = queue_binding.routing_key
            exchange_name = ""

            direction = injection.GenericInjector.DIRECTION_OUT
            if not(routing_key.startswith("reply_")):
                routing_key = self.FAKE_OUT_PREFIX + routing_key
                exchange_name = queue_binding.exchange_name

                direction = injection.GenericInjector.DIRECTION_IN

            assert self.default_injector != None
            body, properties = self.default_injector.inject(f"{exchange_name}_{routing_key}",
                                                            (body, properties),
                                                            direction,
                                                            "AMQP")

            self.LOG.debug(f"ROUTING KEY {routing_key}")

            cliout.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=body,
                properties=properties
            )
            self.LOG.debug('### QUEUE MESSAGE')
            self.LOG.debug(f'EXCHANGE {queue_binding.exchange_name}')
            self.LOG.debug(f'ROUTING KEY {queue_binding.routing_key}')
            self.LOG.debug('#### BEGIN BODY')
            self.LOG.debug('')
            self.LOG.debug(body)
            self.LOG.debug('')
            self.LOG.debug('#### END BODY')
            self.LOG.debug('#### BEGIN PROPERTIES')
            self.LOG.debug('')
            self.LOG.debug(properties)
            self.LOG.debug('')
            self.LOG.debug('#### END PROPERTIES')
            self.LOG.debug('')


            connout.close()
            self.LOG.debug(f'Ch Found')
        else:
            self.LOG.error(f'Ch Not Found')
        self.LOG.debug(f'ack {method.delivery_tag}')

    def start(self):
        if self._mainthread is None:
            self._mainthread = Thread(target=self._start)
            self._mainthread.daemon = True
            self._mainthread.start()

    def stop(self):
        for clichan in self._clichannels:
            clichan.stop_consuming()