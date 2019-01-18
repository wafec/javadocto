

class Input(object):
    def __init__(self, name, args, waits, target):
        self.name = name
        self.args = args
        self.waits = waits
        self.target = target

    def __repr__(self):
        return "Name=%s, Args=%s, Waits=%s, Target=%s" % (self.name, self.args, self.waits, self.target)
