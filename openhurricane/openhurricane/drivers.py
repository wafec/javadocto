import logging
from openhurricane import functions
from openhurricane.base import ComputeTestBase


class ComputeTestDriver(ComputeTestBase):
    LOG = logging.getLogger("ComputeTestDriver")

    def __init__(self, conf):
        self.clear_list = []
        self.functions = [
            functions.ResizeFunction("RESIZE", self),
            functions.StartInstanceFunction("conductor.START_INSTANCE", self),
            functions.ShelveInstanceFunction("SHELVE_INSTANCE", self),
            functions.UnshelveInstanceFunction("UNSHELVE_INSTANCe", self),
            functions.DeleteInstanceFunction("DELETE_INSTANCE", self),
            functions.RebuildFunction("REBUILD", self),
            functions.ResizeFunction("RESIZE", self)
        ]
        super(ComputeTestDriver, self).__init__(conf)

    def setup(self):
        super(ComputeTestDriver, self).setup()
        self.setup_resources()
        self.setup_functions()

    def setup_functions(self):
        for func in self.functions:
            func.setup()

    def setup_resources(self):
        self.setup_images()
        self.setup_flavors()

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

        self.add_clear(self.image_client.images.delete, image_id=image.id)
        return image

    def setup_flavors(self):
        self.flavor = self._create_flavor(self.CONF.resources.flavor)
        self.flavor_alt = self._create_flavor(self.CONF.resources.flavor_alt)

    def _create_flavor(self, item):
        flavor = self.compute_client.flavors.get

        flavor = self.compute_client.flavors.create(name=item.name,
                                            ram=item.ram,
                                            vcpus=item.vcpus,
                                            disk=item.disk
                                            )
        self.add_clear(self.compute_client.flavors.delete, flavor)
        return flavor

    def run_test_input(self, op_name):
        for func in self.functions:
            if func.is_me(op_name):
                func.run()

    def add_clear(self, func, *args, **kwargs):
        self.clear_list.append((func, args, kwargs))

    def clear(self):
        for clear_item in self.clear_list:
            try:
                clear_item[0](*clear_item[1], **clear_item[2])
            except Exception as exception:
                self.LOG.error(exception)

    def create_server(self, name, flavor, image):
        server = self.compute_client.servers.create(name=name,
                                                    flavor=flavor,
                                                    image=image)
        self.add_clear(self.compute_client.servers.delete, server)
        return server

    def __del__(self):
        self.clear()
