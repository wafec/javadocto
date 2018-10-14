import logging
from openhurricane import functions
from openhurricane.base import ComputeTestBase
import time


class ComputeTestDriver(ComputeTestBase):
    LOG = logging.getLogger("ComputeTestDriver")

    def __init__(self, conf):
        self.clear_list = []
        self.functions = [
            functions.StartInstanceFunction("conductor.START_INSTANCE", self),
            functions.ShelveInstanceFunction("conductor.SHELVE_INSTANCE", self),
            functions.UnshelveInstanceFunction("conductor.UNSHELVE_INSTANCE", self),
            functions.DeleteInstanceFunction("conductor.DELETE_INSTANCE", self),
            functions.RebuildFunction("conductor.REBUILD", self),
            functions.ResizeFunction("conductor.RESIZE", self),
            functions.ConfirmFunction("conductor.CONFIRM", self),
            functions.CancelFunction("conductor.CANCEL", self)
        ]
        super(ComputeTestDriver, self).__init__(conf)
        self.current_flavor = None
        self.current_image = None

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

        start = time.time()
        self.LOG.debug(f"Image {image.id} status {image.status}")
        while True:
            image = self.image_client.images.get(image.id)
            elapsed = time.time() - start
            if image.status == "active" or elapsed > 10:
                break
            self.LOG.debug(f"Image {image.id} status {image.status}")
            time.sleep(1)

        self.add_clear(self.image_client.images.delete, image_id=image.id)

        if image.status != "active":
            raise Exception("Image cannot be ACTIVE")

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
                try:
                    func.run()
                except Exception as exception:
                    self.LOG.error(exception)

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

    def _check_flavor(self):
        self.current_flavor = self.current_flavor if self.current_flavor else self.flavor

    def _check_image(self):
        self.current_image = self.current_image if self.current_image else self.image

    def get_current_flavor(self):
        self._check_flavor()
        return self.current_flavor if self.current_flavor else self.flavor

    def get_opposite_flavor(self):
        self._check_flavor()
        return self.flavor if self.current_flavor == self.flavor_alt else self.flavor_alt

    def get_current_image(self):
        self._check_image()
        return self.current_image if self.current_image else self.image

    def get_opposite_image(self):
        self._check_image()
        return self.image if self.current_image == self.image_alt else self.image_alt

    def change_image(self):
        self._check_image()
        self.current_image = self.image if self.current_image != self.image else self.image_alt

    def change_flavor(self):
        self._check_flavor()
        self.current_flavor = self.flavor if self.current_flavor != self.flavor else self.flavor_alt