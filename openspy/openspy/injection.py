class GenericInjector:
    DIRECTION_IN = "__IN__"
    DIRECTION_OUT = "__OUT__"

    def __init__(self):
        self.handler = None

    def inject(self, operation, message, direction=DIRECTION_IN, tag=None):
        if self.handler:
            return self.handler.handle_injection(operation, message, direction, tag)
        return message
