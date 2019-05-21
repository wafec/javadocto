import logging
import datetime
import math


class TimingLogger(object):
    LOG = logging.getLogger('Timing')

    _start = {}
    _description = {}

    @staticmethod
    def start(id, description):
        TimingLogger._log(id)
        TimingLogger.LOG.info('Label=%s, Begin=%s' % (description, datetime.datetime.now().strftime('%b %d %H:%M:%S')))
        TimingLogger._start[id] = datetime.datetime.now()
        TimingLogger._description[id] = description

    @staticmethod
    def stop(id):
        TimingLogger._log(id)
        del TimingLogger._start[id]
        del TimingLogger._description[id]

    @staticmethod
    def _log(id):
        if id in TimingLogger._start:
            total = (datetime.datetime.now() - TimingLogger._start[id]).total_seconds()
            TimingLogger.LOG.info('Total(s)=%s, Label=%s' % (total, TimingLogger._description[id]))


class UnorderedProgress(object):
    def __init__(self, amin, amax, current=0, decimal_places=None):
        self.amin = amin
        self.amax = amax
        self.current = current
        self.decimal_places = decimal_places if decimal_places else int(math.ceil(math.log(amax, 10)))

    def update(self, current=None):
        if current:
            self.current = current
        else:
            self.current += 1

    def incr(self, increment=None):
        self.current += increment if increment else 1

    def __str__(self):
        return '%0{0}d of %{0}d (%05.2f%%)'.format(self.decimal_places) % (self.current, self.amax, (self.current / float(self.amax)) * 100)