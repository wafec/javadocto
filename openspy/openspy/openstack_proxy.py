from keystoneauth1.identity.v3 import Password
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient
import logging
from openspy.model import DBSession, EndpointBackup
from urllib.parse import urlparse
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
import re
import requests
from openspy import injection
import time


class OpenStackBase:
    def __init__(self, conf):
        self.CONF = conf
        password = Password(
            auth_url=conf.auth.url,
            username=conf.auth.username,
            password=conf.auth.password,
            user_domain_id=conf.auth.user_domain_id,
            project_domain_id=conf.auth.project_domain_id,
            project_name=conf.auth.project_name
        )
        self.session = session.Session(auth=password)
        self.identity_client = keystoneclient.Client(session=self.session)


class IdentityFaker(OpenStackBase):
    LOG = logging.getLogger("IdentityFaker")

    def __init__(self, conf):
        super(IdentityFaker, self).__init__(conf)

    def safely_alter_urls(self):
        self.restore_urls()
        self.do_endpoint_backups()
        self.alter_urls()

    def alter_urls(self):
        cli = self.identity_client
        sess = DBSession()
        try:
            for endpoint in cli.endpoints.list():
                service = cli.services.get(endpoint.service_id)
                if service.type not in self.CONF.service_proxy.service_types:
                    self.LOG.warn("Skipping. Service not found.")
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
        test_url = f'{self.CONF.service_proxy.scheme}://{self.CONF.service_proxy.domain}:{self.CONF.service_proxy.port}/{service.type[:2]+service.type[len(service.type)-2:]}{o.path}'
        return test_url

    def do_endpoint_backups(self):
        cli = self.identity_client
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
            cli = self.identity_client
            endpoint_backups = sess.query(EndpointBackup).all()
            for endpoint_backup in endpoint_backups:
                try:
                    cli.endpoints.update(endpoint_backup.endpoint_id, url=endpoint_backup.endpoint_url)
                except Exception:
                    self.LOG.error(f"Endpoint {endpoint_backup.endpoint_id} is not in this OS instance")
                    pass
                sess.delete(endpoint_backup)
            sess.commit()
        finally:
            sess.close()


class OpenStackRestProxy:
    LOG = logging.getLogger("OpenStackRestProxy")
    default_injector = injection.GenericInjector()

    def __init__(self, conf):
        self.CONF = conf
        self._mainthread = None
        self._tserver = None

    def _start(self):
        with ThreadingTCPServer(("", self.CONF.service_proxy.port), self.Handler) as daemon:
            self.LOG.info(f'Listening on address {daemon.server_address}')
            self._tserver = daemon
            daemon.serve_forever()

    def start(self):
        if self._mainthread is not None:
            return
        self._mainthread = Thread(target=self._start)
        self._mainthread.daemon = True
        self._mainthread.start()


    def stop(self):
        if self._mainthread is None:
            return
        if self._tserver is not None:
            self._tserver.shutdown()
            self._tserver.server_close()
        self._mainthread = None

    class Handler(SimpleHTTPRequestHandler):
        LOG = logging.getLogger("ServiceProxy.Handler")
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
                        self.LOG.debug(f'PREFIX {prefix}')
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
            self.LOG.debug(f'{type} {self.path}')
            for key, value in self.headers.items():
                self.LOG.debug(f'Hkey {key}, Hvalue {value}')
            qualified_endpoint_url = self.get_qualified_endpoint_url()
            self.LOG.debug(f'{qualified_endpoint_url}')
            x = self._make_request(type, qualified_endpoint_url)
            self.send_response(x.status_code)
            self.LOG.debug(x.status_code)
            for key, value in x.headers.items():
                self.LOG.debug(f'Hkey {key}, Hvalue {value}')
                self.send_header(key, value)
            self.end_headers()

            bcontent = x.raw.read()
            self.wfile.write(bcontent)
            #shutil.copyfileobj(x.raw, self.wfile)

            self.LOG.debug(f"OUT '{bcontent.decode('utf-8')}'")

            self.wfile.flush()

        def _make_request(self, type, qualified_endpoint_url):
            data = None
            files = None
            headers = dict(self.headers)
            if 'Host' in headers:
                o = urlparse(qualified_endpoint_url)
                self.LOG.warn(f'Q"{qualified_endpoint_url}", NETLOC"{o.netloc}""')
                headers['Host'] = f"{o.netloc}"
                self.LOG.warn(f'Host {headers["Host"]}')

            if type == self._POST or type == self._PUT:
                if 'Content-Length' in self.headers:
                    data = self.rfile.read(int(self.headers['Content-Length']))
                    self.LOG.debug(f'{data}')
                else:
                    self.LOG.error("Haaaaa!!")
                    raise Exception()

            headers, data, files = OpenStackRestProxy.default_injector.inject(
                qualified_endpoint_url,
                (headers, data, files),
                injection.GenericInjector.DIRECTION_IN,
                "HTTP"
            )

            result = None
            if type == self._GET:
                result = requests.get(qualified_endpoint_url, headers=headers, stream=True)
            elif type == self._POST:
                result = requests.post(qualified_endpoint_url, headers=headers, stream=True, data=data, files=files)
            elif type == self._PUT:
                result = requests.put(qualified_endpoint_url, headers=headers, stream=True, data=data, files=files)
            elif type == self._DELETE:
                result = requests.delete(qualified_endpoint_url, headers=headers, stream=True, data=data)

            result = OpenStackRestProxy.default_injector.inject(
                qualified_endpoint_url,
                result,
                injection.GenericInjector.DIRECTION_OUT,
                "HTTP"
            )

            return result

        def do_GET(self):
            self._exec(self._GET)

        def do_POST(self):
            self._exec(self._POST)

        def do_DELETE(self):
            self._exec(self._DELETE)

        def do_PUT(self):
            self._exec(self._PUT)