import logging
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystoneclient
from novaclient import client as novaclient
from glanceclient import client as glanceclient
from openhurricane import functions


class ComputeTestDriver:
    LOG = logging.getLogger("ComputeTestDriver")

    def __init__(self, conf):
        self.CONF = conf
        self.auth = None
        self.session = None
        self.identity_client = None
        self.compute_client = None
        self.image_client = None
        self.functions = [
            functions.ResizeFunction("RESIZE", self)
        ]

        self.setup()

    def setup(self):
        self.setup_clients()
        self.setup_resources()
        self.setup_functions()

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

    def setup_functions(self):
        for func in self.functions:
            func.setup()

    def setup_resources(self):
        self.setup_images()
        self.setup_flavors()
        self.setup_servers()

    def setup_images(self):
        self.image = self._create_image(self.CONF.resources.image)
        self.image_alt = self._create_image(self.CONF.resources.image_alt)

    def _create_image(self, item):
        image = self.image_client.images.create(
                                        disk_format=item.disk_format,
                                        name=item.name,
                                        container_format=item.container_format,
                                        visibility=item.visibility)
        with open(item.data_file, "rb") as image_file:
            self.image_client.images.upload(image_id=image.id,
                                     image_data=image_file)
        return image

    def setup_flavors(self):
        self.flavor = self._create_flavor(self.CONF.resources.flavor)
        self.flavor_alt = self._create_flavor(self.CONF.resources.flavor_alt)

    def _create_flavor(self, item):
        flavor = self.compute_client.flavors.create(name=item.name,
                                            ram=item.ram,
                                            vcpus=item.vcpus,
                                            disk=item.disk
                                            )
        return flavor

    def setup_servers(self):
        self.server = self._create_server(self.CONF.resources.server)

    def _create_server(self, item):
        server = self.compute_client.servers.create(name=item.name,
                                            image=self.image,
                                            flavor=self.flavor)
        return server

    def run_test_input(self, op_name):
        for func in self.functions:
            if func.is_me(op_name):
                func.run()

    def clear(self):
        self.compute_client.servers.delete(self.server)
        self.compute_client.flavors.delete(self.flavor)
        self.compute_client.flavors.delete(self.flavor_alt)
        self.image_client.images.delete(image_id=self.image.id)
        self.image_client.images.delete(image_id=self.image_alt.id)
