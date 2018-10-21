from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from urllib.parse import urlparse
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
import logging
import re
import requests
import shutil
import pika
import json
from hypothesis.strategies import text, characters
from hypothesis import given
import random
import io
from munch import munchify

from ostest.model import DBSession, EndpointBackup
from ostest import config

CONF = config.CONF


class BaseOSTestAgent():
    def _make_session(self):
        auth = v3.Password(auth_url=CONF.auth.url,
                           username=CONF.auth.username,
                           password=CONF.auth.password,
                           user_domain_id=CONF.auth.user_domain_id,
                           project_domain_id=CONF.auth.project_domain_id,
                           project_name=CONF.auth.project_name)
        sess = session.Session(auth=auth)
        return sess

    def _make_client(self):
        sess = self._make_session()
        cli = client.Client(session=sess)
        return cli


class KeystoneOSTestAgent(BaseOSTestAgent):
    log = logging.getLogger("KeystoneTestAgent")

    def safely_alter_urls(self):
        self.restore_urls()
        self.do_endpoint_backups()
        self.alter_urls()

    def alter_urls(self):
        cli = self._make_client()
        sess = DBSession()
        try:
            for endpoint in cli.endpoints.list():
                service = cli.services.get(endpoint.service_id)
                if service.type not in CONF.service_proxy.service_types:
                    self.log.warn("Skipping. Service not found.")
                    continue
                new_url = self._define_test_url(endpoint, service)
                cli.endpoints.update(endpoint=endpoint.id, url=new_url)
                endpoint_backup = sess.query(EndpointBackup).filter(EndpointBackup.endpoint_id == endpoint.id).one()
                endpoint_backup.reference_url = new_url
            sess.commit()
        finally:
            sess.close()

    def _define_test_url(self, endpoint, service):
        current_url = endpoint.url
        o = urlparse(current_url)
        test_url = f'{CONF.service_proxy.scheme}://{CONF.service_proxy.domain}:{CONF.service_proxy.port}/{service.type[:2]+service.type[len(service.type)-2:]}{o.path}'
        return test_url

    def do_endpoint_backups(self):
        cli = self._make_client()
        sess = DBSession()
        try:
            for endpoint in cli.endpoints.list():
                endpoint_backup = EndpointBackup()
                endpoint_backup.endpoint_id = endpoint.id
                endpoint_backup.endpoint_url = endpoint.url
                sess.add(endpoint_backup)
            sess.commit()
        finally:
            sess.close()

    def restore_urls(self):
        sess = DBSession()
        try:
            cli = self._make_client()
            endpoint_backups = sess.query(EndpointBackup).all()
            for endpoint_backup in endpoint_backups:
                try:
                    cli.endpoints.update(endpoint_backup.endpoint_id, url=endpoint_backup.endpoint_url)
                except Exception:
                    self.log.error(f"Endpoint {endpoint_backup.endpoint_id} is not in this OS instance")
                    pass
                sess.delete(endpoint_backup)
            sess.commit()
        finally:
            sess.close()


class ServiceProxy:
    log = logging.getLogger("ServiceProxy")

    def __init__(self):
        self._mainthread = None
        self._tserver = None

    def _start(self):
        with ThreadingTCPServer(("", CONF.service_proxy.port), self.Handler) as daemon:
            self.log.info(f'Listening on address {daemon.server_address}')
            self._tserver = daemon
            daemon.serve_forever()

    def start(self):
        if self._mainthread is not None:
            return
        self._mainthread = Thread(target=self._start)
        self._mainthread.start()

    def stop(self):
        if self._mainthread is None:
            return
        if self._tserver is not None:
            self._tserver.shutdown()
            self._tserver.server_close()
        self._mainthread = None

    class Handler(SimpleHTTPRequestHandler):
        log = logging.getLogger("ServiceProxy.Handler")
        _GET = 'GET'
        _POST = 'POST'
        _PUT = 'PUT'
        _DELETE = 'DELETE'

        def get_qualified_endpoint_url(self):
            sess = DBSession()
            try:
                for endpoint_backup in sess.query(EndpointBackup).all():
                    endpoint_path = str(urlparse(endpoint_backup.reference_url).path)
                    m = re.search(r'(/\w+/\w+/)', endpoint_path)
                    if m:
                        prefix = m.group(0)
                        self.log.debug(f'PREFIX {prefix}')
                        if self.path.startswith(prefix):
                            o = urlparse(endpoint_backup.endpoint_url)
                            return f'{o.scheme}://{o.netloc}{self.path[5:]}'

                    r = re.sub(r"\$\([\w_]+\)s", "[a-zA-Z0-9]+", str(urlparse(endpoint_backup.reference_url).path))
                    m = re.compile(r + ".*")
                    if m.match(self.path):
                        o = urlparse(endpoint_backup.endpoint_url)
                        return f'{o.scheme}://{o.netloc}{self.path[5:]}'
                raise ValueError(f'Invalid URL "{self.path}"')
            finally:
                sess.close()

        def _exec(self, type):
            self.log.debug(f'{type} {self.path}')
            for key, value in self.headers.items():
                self.log.debug(f'Hkey {key}, Hvalue {value}')
            qualified_endpoint_url = self.get_qualified_endpoint_url()
            self.log.debug(f'{qualified_endpoint_url}')
            x = self._make_request(type, qualified_endpoint_url)
            self.send_response(x.status_code)
            self.log.debug(x.status_code)
            for key, value in x.headers.items():
                self.log.debug(f'Hkey {key}, Hvalue {value}')
                self.send_header(key, value)
            self.end_headers()

            bcontent = x.raw.read()
            self.wfile.write(bcontent)
            #shutil.copyfileobj(x.raw, self.wfile)

            self.log.debug(f"OUT '{bcontent.decode('utf-8')}'")

            self.wfile.flush()

        def _make_request(self, type, qualified_endpoint_url):
            data = None
            files = None
            headers = dict(self.headers)
            if 'Host' in headers:
                o = urlparse(qualified_endpoint_url)
                self.log.warn(f'Q"{qualified_endpoint_url}", NETLOC"{o.netloc}""')
                headers['Host'] = f"{o.netloc}"
                self.log.warn(f'Host {headers["Host"]}')

            if type == self._POST or type == self._PUT:
                data = self.rfile.read(int(self.headers['Content-Length']))
                self.log.debug(f'{data}')
            if type == self._GET:
                return requests.get(qualified_endpoint_url, headers=headers, stream=True)
            elif type == self._POST:
                return requests.post(qualified_endpoint_url, headers=headers, stream=True, data=data, files=files)
            elif type == self._PUT:
                return requests.put(qualified_endpoint_url, headers=headers, stream=True, data=data, files=files)
            elif type == self._DELETE:
                return requests.delete(qualified_endpoint_url, headers=headers, stream=True, data=data)
            return None

        def do_GET(self):
            self._exec(self._GET)

        def do_POST(self):
            self._exec(self._POST)

        def do_DELETE(self):
            self._exec(self._DELETE)

        def do_PUT(self):
            self._exec(self._PUT)


class BaseRabbit:
    FAKE_IN_PREFIX = "FAKEIN_"
    FAKE_OUT_PREFIX = "FAKEOUT_"

    def _make_channel(self):
        credentials = pika.PlainCredentials(CONF.rabbit.username, CONF.rabbit.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            CONF.rabbit.host,
            CONF.rabbit.port,
            CONF.rabbit.vhost,
            credentials
        ))
        return connection.channel(), connection


class RabbitTestAgent(BaseRabbit):
    def __init__(self):
        pass

    def alter_bindings(self):
        cha, _ = self._make_channel()
        for queue_binding in CONF.rabbit.queue.bindings:
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
        cha, _ = self._make_channel()
        for queue_binding in CONF.rabbit.queue.bindings:
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


class QueueProxy(BaseRabbit):
    log = logging.getLogger("QueueProxy")
    FUZZ_ENABLED = False

    def __init__(self):
        self._mainthread = None
        self._clithreads = []
        self._clichannels = []
        self._queue_bindings = []

    def _start(self):
        self._initialize(CONF.rabbit.queue.bindings)

    def _initialize(self, queue_bindings):
        for queue_binding in queue_bindings:
            cha, _ = self._make_channel()
            self._clichannels.append(cha)
            t = Thread(target=self._start_cli, args=[cha, queue_binding])
            self._clithreads.append(t)
            self._queue_bindings.append(queue_binding)
            t.start()

    def _start_cli(self, cha, queue_binding):
        cha.basic_consume(self._callback, queue=self.FAKE_IN_PREFIX + queue_binding.queue_name, no_ack=True)
        cha.start_consuming()

    def _get_ch_index(self, ch):
        for i in range(0, len(self._clichannels)):
            if self._clichannels[i] == ch:
                return i
        return -1

    def _exec_fuzzer(self, exchange, routing_key, body, properties):
        obj = json.loads(body)
        message = json.loads(obj["oslo.message"])
        cli, conn = self._make_channel()
        random.seed()

        def _rec(obj, parent):
            self.log.debug(f'Type {type(parent)}')
            if isinstance(parent, dict):
                for key, value in parent.items():
                    _rec(obj, value)
                    if isinstance(value, str):
                        @given(text())
                        def _inner_s(name):
                            parent[key] = name
                            self.log.debug(f'FuzzAct Key {key}, Fake {name}, Value {value}')
                            data = json.loads(body)
                            data["oslo.message"] = json.dumps(message)
                            try:
                                cli.basic_publish(
                                    exchange=exchange, routing_key=routing_key,
                                    properties=properties, body=bytes(json.dumps(data), 'utf-8')
                                )
                            except Exception as ex:
                                self.log.error(ex)
                            parent[key] = value

                        n = random.uniform(0, 1)
                        self.log.debug(f'RANDOM {n}')
                        if n < .15 or n > .85:
                            _inner_s()
        _rec(obj, message)

        conn.close()

    def _make_a_bind_if_needed(self, oslo_message):
        if "_reply_q" in oslo_message and oslo_message["_reply_q"]:
            self.log.debug(f"Making a reply to {oslo_message['_reply_q']}")
            direct_name = oslo_message["_reply_q"]
            cha, _ = self._make_channel()

            cha.queue_declare(
                queue=self.FAKE_IN_PREFIX + direct_name
            )
            cha.exchange_declare(
                exchange=self.FAKE_IN_PREFIX + direct_name
            )

            self.log.debug(f"Queue and exchange names are {self.FAKE_IN_PREFIX + direct_name}")

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
        self.log.debug(f'[x] {method.routing_key}')
        i = self._get_ch_index(ch)
        if i >= 0:
            queue_binding = self._queue_bindings[i]
            self.log.warn(f'[x] {self.FAKE_OUT_PREFIX + queue_binding.routing_key}')
            cliout, connout = self._make_channel()

            message = json.loads(body)
            oslo_message = self._make_a_bind_if_needed(json.loads(message["oslo.message"]))
            message["oslo.message"] = oslo_message
            body = json.dumps(message)

            # BEGIN FUZZ
            if self.FUZZ_ENABLED:
                self._exec_fuzzer(
                    exchange=queue_binding.exchange_name,
                    routing_key=self.FAKE_OUT_PREFIX + queue_binding.routing_key,
                    body=body,
                    properties=properties
                 )
            # END FUZZ

            for _ in range(0, 1):
                routing_key = queue_binding.routing_key
                exchange_name = ""

                if not(routing_key.startswith("reply_")):
                    routing_key = self.FAKE_OUT_PREFIX + routing_key
                    exchange_name = queue_binding.exchange_name

                self.log.debug(f"ROUTING KEY {routing_key}")

                cliout.basic_publish(
                    exchange=exchange_name,
                    routing_key=routing_key,
                    body=body,
                    properties=properties
                )
                self.log.warn("Calling again")
                print('### QUEUE MESSAGE')
                print(f'EXCHANGE {queue_binding.exchange_name}')
                print(f'ROUTING KEY {queue_binding.routing_key}')
                print('#### BEGIN BODY')
                print('')
                print(body)
                print('')
                print('#### END BODY')
                print('#### BEGIN PROPERTIES')
                print('')
                print(properties)
                print('')
                print('#### END PROPERTIES')
                print('')


            connout.close()
            self.log.debug(f'Ch Found')
        else:
            self.log.error(f'Ch Not Found')
        self.log.debug(f'ack {method.delivery_tag}')

    def start(self):
        if self._mainthread is None:
            self._mainthread = Thread(target=self._start)
            self._mainthread.start()

    def stop(self):
        for clichan in self._clichannels:
            clichan.stop_consuming()