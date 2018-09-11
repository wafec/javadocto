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

from ostest.model import DBSession, EndpointBackup
from ostest import config

CONF = config.CONF


class BaseTestAgent():
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


class KeystoneTestAgent(BaseTestAgent):
    log = logging.getLogger("KeystoneTestAgent")

    def safely_alter_urls(self):
        self.restore_urls()
        self.do_endpoint_backups()
        self.alter_urls()

    def alter_urls(self):
        cli = self._make_client()
        sess = DBSession()
        for endpoint in cli.endpoints.list():
            service = cli.services.get(endpoint.service_id)
            if service.type != "compute" and service.type != "image":
                self.log.warn("Skipping mismatching configuration")
                continue
            new_url = self._define_test_url(endpoint, service)
            cli.endpoints.update(endpoint=endpoint.id, url=new_url)
            endpoint_backup = sess.query(EndpointBackup).filter(EndpointBackup.endpoint_id == endpoint.id).one()
            endpoint_backup.reference_url = new_url
        sess.commit()

    def _define_test_url(self, endpoint, service):
        current_url = endpoint.url
        o = urlparse(current_url)
        test_url = f'{CONF.service_proxy.scheme}://{CONF.service_proxy.domain}:{CONF.service_proxy.port}/{service.type[:2]}{o.path}'
        return test_url

    def do_endpoint_backups(self):
        cli = self._make_client()
        sess = DBSession()
        for endpoint in cli.endpoints.list():
            endpoint_backup = EndpointBackup()
            endpoint_backup.endpoint_id = endpoint.id
            endpoint_backup.endpoint_url = endpoint.url
            sess.add(endpoint_backup)
        sess.commit()

    def restore_urls(self):
        sess = DBSession()
        cli = self._make_client()
        endpoint_backups = sess.query(EndpointBackup).all()
        for endpoint_backup in endpoint_backups:
            cli.endpoints.update(endpoint_backup.endpoint_id, url=endpoint_backup.endpoint_url)
            sess.delete(endpoint_backup)
        sess.commit()


class ServiceProxy:
    log = logging.getLogger("ServiceProxy")

    def __init__(self):
        self._mainthread = None
        self._tserver = None

    def _start_server(self):
        with ThreadingTCPServer(("", CONF.service_proxy.port), self.Handler) as daemon:
            self.log.info(f'Listening on address {daemon.server_address}')
            self._tserver = daemon
            daemon.serve_forever()

    def start_server(self):
        if self._mainthread is not None:
            return
        self._mainthread = Thread(target=self._start_server)
        self._mainthread.start()

    def stop_server(self):
        if self._mainthread is None:
            return
        self._tserver.shutdown()
        self._tserver.server_close()
        self._mainthread = None

    class Handler(SimpleHTTPRequestHandler):
        log = logging.getLogger("ServiceProxy.Handler")

        def get_qualified_endpoint_url(self):
            sess = DBSession()
            for endpoint_backup in sess.query(EndpointBackup).all():
                r = re.sub(r"\$\([\w_]+\)s", "[a-zA-Z0-9]+", str(urlparse(endpoint_backup.reference_url).path))
                m = re.compile(r + ".*")
                if m.match(self.path):
                    o = urlparse(endpoint_backup.endpoint_url)
                    return f'{o.scheme}://{o.netloc}{self.path[3:]}'
            raise ValueError('Invalid URL')

        def _exec(self, type):
            data = None
            files = None
            self.log.debug(f'{type} {self.path}')
            for key, value in self.headers.items():
                self.log.debug(f'Hkey {key}, Hvalue {value}')
            qualified_endpoint_url = self.get_qualified_endpoint_url()
            self.log.debug(f'{qualified_endpoint_url}')
            if type == 'POST' or type == 'PUT':
                data = self.rfile.read()
                self.log.debug(f'{data}')
            if type == 'GET':
                x = requests.get(qualified_endpoint_url, headers=self.headers, stream=True)
            elif type == 'POST':
                x = requests.post(qualified_endpoint_url, headers=self.headers, stream=True, data=data, files=files)
            elif type == 'PUT':
                x = requests.put(qualified_endpoint_url, headers=self.headers, stream=True, data=data, files=files)
            elif type == 'DELETE':
                x = requests.delete(qualified_endpoint_url, headers=self.headers, stream=True, data=data)
            self.send_response(x.status_code)
            self.log.debug(x.status_code)
            for key, value in x.headers.items():
                self.log.debug(f'Hkey {key}, Hvalue {value}')
                self.send_header(key, value)
            self.end_headers()
            shutil.copyfileobj(x.raw, self.wfile)
            self.wfile.flush()

        def do_GET(self):
            self._exec('GET')

        def do_POST(self):
            self._exec('POST')

        def do_DELETE(self):
            self._exec('DELETE')

        def do_PUT(self):
            self._exec('PUT')
