import logging
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class Interceptor(object):
    def __init__(self, amqp_url, exchange, exchange_type, queue, routing_key):
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._queue = queue
        self._queue_aux = '%s_aux' % queue
        self._routing_key = routing_key
        self._routing_key_aux = '%s_aux' % routing_key
        self._on_running_callback = []
        self._on_message_callback = None

    def add_on_running_callback(self, on_running_callback):
        self._on_running_callback.append(on_running_callback)

    def connect(self):
        LOGGER.info('Connecting to %s', self._url)
        return pika.SelectConnection(pika.URLParameters(self._url),
                                     self.on_connection_open)

    def on_connection_open(self, unused_connection):
        LOGGER.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        LOGGER.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s', reply_code, reply_text)
            self._connection.ioloop.call_later(5, self.reconnect)

    def reconnect(self):
        self._connection.ioloop.stop()

        if not self._closing:
            self._connection = self.connect()
            self._connection.ioloop.start()

    def open_channel(self):
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self._exchange)

    def add_on_channel_close_callback(self):
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        LOGGER.warning('Channel %i was closed: (%s) %s', channel, reply_code, reply_text)
        self._connection.close()

    def setup_exchange(self, exchange_name):
        LOGGER.info('Declaring exchange: %s', exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self._exchange_type)

    def on_exchange_declareok(self, unused_frame):
        LOGGER.info('Exchange declared')
        self.setup_queue(self._queue)

    def setup_queue(self, queue_name):
        LOGGER.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name)

    def on_queue_declareok(self, method_frame):
        LOGGER.info('Queue declared')
        self.setup_queue_aux(self._queue_aux)

    def setup_queue_aux(self, queue_name):
        LOGGER.info('Declaring queue aux')
        self._channel.queue_declare(self.on_queue_aux_declareok, queue_name)

    def on_queue_aux_declareok(self, method_frame):
        LOGGER.info('Queue aux declared')
        LOGGER.info('Binding %s to %s with %s',
                    self._exchange, self._queue_aux, self._routing_key)
        self._channel.queue_bind(self.on_queue_aux_bindok, self._queue_aux,
                                 self._exchange, self._routing_key)

    def on_queue_aux_bindok(self, unused_frame):
        LOGGER.info('Queue aux bound')
        LOGGER.info('Binding %s to %s with %s',
                    self._exchange, self._queue, self._routing_key_aux)
        self._channel.queue_bind(self.on_queue_bindok, self._queue,
                                 self._exchange, self._routing_key_aux)

    def on_queue_bindok(self, unused_frame):
        LOGGER.info('Queue bound')
        LOGGER.info('Unbinding %s to %s with %s',
                    self._exchange, self._queue, self._routing_key)
        self._channel.queue_unbind(self.on_queue_unbindok, self._queue,
                                   self._exchange, self._routing_key)

    def on_queue_unbindok(self, unused_frame):
        LOGGER.info('Queue unbound')
        self.start_consuming()

    def start_consuming(self):
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self.enable_delivery_confirmations()
        self.call_on_running_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message, self._queue_aux)

    def call_on_running_callback(self):
        for on_running_callback in self._on_running_callback:
            on_running_callback()

    def enable_delivery_confirmations(self):
        LOGGER.info('Issuing Confirm.Select RPC command')
        self._channel.confirm_delivery(self.on_delivery_confirmation)

    def on_delivery_confirmation(self, method_frame):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        LOGGER.info('Received %s for delivery tag: %i',
                    confirmation_type,
                    method_frame.method.delivery_tag)
        self.acknowledge_message(method_frame.method.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        LOGGER.info('Acknowledging message: %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def add_on_cancel_callback(self):
        LOGGER.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        LOGGER.info('Received message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)

        new_body = self.call_on_message_callback(body)

        self.deliver_message(properties, body if new_body is None else new_body)

    def call_on_message_callback(self, body):
        if self._on_message_callback:
            return self._on_message_callback(body)
        return None

    def add_on_message_callback(self, on_message_callback):
        self._on_message_callback = on_message_callback

    def deliver_message(self, properties, body):
        if self._channel is None or not self._channel.is_open:
            return

        self._channel.basic_publish(self._exchange, self._routing_key_aux,
                                    body, properties)

    def stop_consuming(self):
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def close_channel(self):
        LOGGER.info('Closing the channel')
        self._channel.close()

    def run(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        LOGGER.info('Stopping')
        self._closing = True
        self.restore_binding()
        self._connection.ioloop.start()
        LOGGER.info('Stopped')

    def restore_binding(self):
        LOGGER.info('Restoring binding')
        LOGGER.info('Binding %s to %s with %s',
                    self._exchange, self._queue, self._routing_key)
        self._channel.queue_bind(self.on_bindok, self._queue, self._exchange,
                                 self._routing_key)

    def on_bindok(self, unused_frame):
        LOGGER.info('Queue bound')
        LOGGER.info('Unbinding %s to %s with %s',
                    self._exchange, self._queue_aux, self._routing_key)
        self._channel.queue_unbind(self.on_unbindok, self._queue_aux, self._exchange,
                                   self._routing_key)

    def on_unbindok(self, unused_frame):
        LOGGER.info('Queue unbound')
        self.stop_consuming()

    def close_connection(self):
        LOGGER.info('Closing connection')
        self._connection.close()


def example_interceptor():
    example = Interceptor('amqp://stackrabbit:supersecret@localhost:5672/%2F',
                          exchange='nova', exchange_type='topic',
                          queue='conductor', routing_key='conductor')
    return example


def main():
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    example = example_interceptor()
    try:
        example.run()
    except KeyboardInterrupt:
        example.stop()


if __name__ == '__main__':
    main()