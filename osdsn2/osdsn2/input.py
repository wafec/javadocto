

class Input(object):
    def __init__(self, name, args, waits, state_trans, timeout_p1=None, timeout_p2=None):
        self.name = name
        self.args = args
        self.waits = waits
        self.state_trans = state_trans
        self.visited = False
        self.used = False
        self.conflicting = False
        self.fault_message = None
        self.timeout_p1 = timeout_p1
        self.timeout_p2 = timeout_p2

    def __repr__(self):
        return "Name=%s, Args=%s, Waits=%s, Target=%s, Visited=%s, Used=%s, Conflicting=%s, Fault=%s" % \
               (self.name, self.args, self.waits, self.state_trans, self.visited, self.used, self.conflicting,
                self.fault_message)
