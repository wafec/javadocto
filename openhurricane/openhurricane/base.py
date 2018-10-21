from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient
from novaclient import client as novaclient
from glanceclient import client as glanceclient


class ComputeTestBase:
    def __init__(self, conf):
        self.CONF = conf
        self.auth = None
        self.session = None
        self.identity_client = None
        self.compute_client = None
        self.image_client = None

        self.setup()

    def setup_clients(self):
        self.auth = v3.Password(auth_url=self.CONF.auth.url,
                                username=self.CONF.auth.username,
                                password=self.CONF.auth.password,
                                user_domain_id=self.CONF.auth.user_domain_id,
                                project_domain_id=self.CONF.auth.project_domain_id,
                                project_name=self.CONF.auth.project_name)
        self.session = session.Session(auth=self.auth)
        self.identity_client = keystoneclient.Client(session=self.session)
        self.compute_client = novaclient.Client(session=self.session, version="2")
        self.image_client = glanceclient.Client(session=self.session, version="2")

    def setup(self):
        self.setup_clients()