from faker import Faker


class BaseFunction:
    def __init__(self, name):
        self.name = name

    def is_me(self, name):
        return self.name == name

    def setup(self):
        pass

    def run(self):
        pass


class ResizeFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(ResizeFunction, self).__init__(name)
        self.test_driver = test_driver

    def run(self):
        flavor = self.test_driver.get_opposite_flavor()
        self.test_driver.compute_client.servers.resize(self.test_driver.server, flavor)


class RebuildFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(RebuildFunction, self).__init__(name)
        self.test_driver = test_driver
        self._image_ref = False

    def run(self):
        image = self.test_driver.get_opposite_image()
        self.test_driver.compute_client.servers.rebuild(self.test_driver.server, image)
        self.test_driver.change_image()


class StartInstanceFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(StartInstanceFunction, self).__init__(name)
        self.test_driver = test_driver
        self._fake = Faker()

    def run(self):
        self.test_driver.server = self.test_driver.create_server(
            self._fake.name(), image=self.test_driver.image, flavor=self.test_driver.flavor
        )


class ShelveInstanceFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(ShelveInstanceFunction, self).__init__(name)
        self.test_driver = test_driver

    def run(self):
        self.test_driver.compute_client.servers.shelve(self.test_driver.server)


class UnshelveInstanceFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(UnshelveInstanceFunction, self).__init__(name)
        self.test_driver = test_driver

    def run(self):
        self.test_driver.compute_client.servers.unshelve(self.test_driver.server)


class DeleteInstanceFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(DeleteInstanceFunction, self).__init__(name)
        self.test_driver = test_driver

    def run(self):
        self.test_driver.compute_client.servers.delete(self.test_driver.server)


class ConfirmFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(ConfirmFunction, self).__init__(name)
        self.test_driver = test_driver

    def run(self):
        self.test_driver.compute_client.servers.confirm_resize(self.test_driver.server)
        self.test_driver.change_flavor()


class CancelFunction(BaseFunction):
    def __init__(self, name, test_driver):
        super(CancelFunction, self).__init__(name)
        self.test_driver = test_driver

    def run(self):
        self.test_driver.compute_client.servers.revert_resize(self.test_driver.server)