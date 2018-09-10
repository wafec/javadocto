from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler
import logging
from threading import Thread
from socketserver import ThreadingTCPServer
import re
import urllib.request
import requests
import uuid

from ostest import config, model

CONF = config.CONF


class ApiProxy():
    log = logging.getLogger("ApiProxy")

    def __init__(self):
        self.httpd = None
        self.httpd_thread = None

    def alter_original_endpoints(self):

        session = model.DBSession()
        self.restore_original_endpoints()
        endpoints = session.query(model.Endpoint).all()
        for endpoint in endpoints:
            new_url = self._get_new_url(endpoint)
            if endpoint.url != new_url:
                endpoint_bkp = model.EndpointBkp()
                endpoint_bkp.url = endpoint.url
                endpoint_bkp.endpoint = endpoint
                endpoint_bkp.endpoint_id = endpoint.id
                session.add(endpoint_bkp)
                endpoint.url = new_url
            else:
                self.log.warn(f"Seems there exist a duplicate in the database for endpoint.id = {endpoint.id}")
        session.commit()
        self.log.debug("Original endpoints altered with success")

    def _get_new_url(self, endpoint):
        o = urlparse(endpoint.url)
        new_url = CONF.service_proxy.schema + "://localhost" + ':' + str(CONF.service_proxy.port) + '/' + endpoint.service.type[:2] + o.path
        return new_url

    def restore_original_endpoints(self):
        session = model.DBSession()
        endpoints_bkp = session.query(model.EndpointBkp).all()

        if len(endpoints_bkp) is 0:
            self.log.debug("None endpoints_bkp to restore")
            return

        for endpoint_bkp in endpoints_bkp:
            if endpoint_bkp.url == None:
                self.log.warn(f"Weird but a None value was encountered in endpoint_bkp.id = {endpoint_bkp.id}")
                continue
            endpoint_bkp.endpoint.url = endpoint_bkp.url
            session.delete(endpoint_bkp)
        session.commit()
        self.log.debug("Original endpoints restored with success")

    def _run_forever(self):
        with ThreadingTCPServer(("", CONF.service_proxy.port), ApiProxyHandler) as self.httpd:
            self.httpd.serve_forever()

    def start(self):
        if self.httpd_thread is not None:
            self.log.error("Http is already active")
            return

        self.httpd_thread = Thread(target=self._run_forever)
        self.httpd_thread.start()
        self.log.debug("Httpd thread started")

    def stop(self):
        if self.httpd_thread is not None and self.httpd is not None:
            self.log.debug("Going to stop httpd")
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd_thread = None
            self.httpd = None
            self.log.debug("Httpd stopped")
        else:
            self.log.error("There is no running httpd process to stop it")


class ApiProxyHandler(SimpleHTTPRequestHandler):
    log = logging.getLogger("ApiProxyHandler")

    def _do_SOMETHING(self, m):
        cuid = uuid.uuid4()
        self.log.debug(f"Begin of {cuid}")
        data = None
        if 'Content-Length' in self.headers:
            data = self.rfile.read(int(self.headers['Content-Length']))
        headers = self.headers
        original_url = self._get_original_url()

        if original_url is None:
            self.log.error(f"'{self.path}' is not a valid URL")
            return

        self.log.debug(f"Sending request to '{original_url}'")
        self.log.debug(f"Sending following data '{str(data)}'")
        self.log.debug(f"Sending following headers '{headers}'")
        response = m(original_url, headers=headers, data=data)
        self.log.debug("Request returned")
        self.send_response(response.status_code)
        for key in response.headers:
            value = response.headers[key]
            self.send_header(key, value)
        self.end_headers()
        self.log.debug(f"Response data is '{response.text}'")
        self.wfile.write(bytes(response.text, 'utf-8'))
        self.log.debug(f"End of {cuid}")

    def do_GET(self):
        url = self._get_original_url()
        self.log.debug(f"[GET] {url}")
        r = requests.get(url)
        self.log.debug(f"[RESPONSE] {r}")
        self.send_response(r.status_code)
        for key in r.headers:
            value = r.headers[key]
            self.send_header(key, value)
        self.end_headers()
        self.log.debug(f"Response data is '{r.text}'")
        self.wfile.write(bytes(r.text, 'utf-8'))

    def do_POST(self):
        self.log.debug("[POST] handling request")
        self._do_SOMETHING(requests.post)

    def do_DELETE(self):
        self.log.debug("[DELETE] handling request")
        self._do_SOMETHING(requests.delete)

    def do_PUT(self):
        self.log.debug("[PUT] handling request")
        self._do_SOMETHING(requests.put)

    def _get_original_url(self):
        session = model.DBSession()
        endpoints_bkp = session.query(model.EndpointBkp).all()
        for endpoint_bkp in endpoints_bkp:
            if self._it_matches(endpoint_bkp):
                original_path = self.path[3:]
                o = urlparse(endpoint_bkp.url)
                return o.scheme + "://" + o.netloc + original_path
        self.log.warn(f"None correspondences for {self.path}")
        return None

    def _it_matches(self, endpoint_bkp):
        o = urlparse(endpoint_bkp.endpoint.url)
        path_bkp = re.compile(r'\$\([\w_]+\)s').sub('[a-zA-Z0-9]+/', o.path)
        path_bkp = "" + path_bkp + ".*"
        self.log.debug(f"Using pattern '{path_bkp}' for {o.path}")
        if re.compile(path_bkp, re.IGNORECASE).match(self.path):
            self.log.debug(f"'{self.path}' has matched")
            return True
        return False