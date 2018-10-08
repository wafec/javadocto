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
        pass