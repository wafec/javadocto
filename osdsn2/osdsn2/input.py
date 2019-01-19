

class Input(object):
    def __init__(self, name, args, waits, state_trans):
        self.name = name
        self.args = args
        self.waits = waits
        self.state_trans = state_trans

    def __repr__(self):
        return "Name=%s, Args=%s, Waits=%s, Target=%s" % (self.name, self.args, self.waits, self.state_trans)
