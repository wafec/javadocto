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
        self.start_time = datetime.datetime.now()
        self.last_update = datetime.datetime.now()
        self.elapsed_time = datetime.datetime.now() - self.last_update

    def update(self, current=None):
        if current:
            self.current = current
        else:
            self.current += 1
        self.elapsed_time += datetime.datetime.now() - self.last_update
        self.last_update = datetime.datetime.now()

    def incr(self, increment=None):
        self.current += increment if increment else 1

    def __str__(self):
        x = self.amax * ((datetime.datetime.now() - self.start_time).total_seconds() / self.current)
        estimated_time = self.start_time + datetime.timedelta(0, x)
        return '%0{0}d of %{0}d (%05.2f%%) {1} {2} < {3} < {4}'.format(self.decimal_places, str(estimated_time - self.start_time).split('.')[0],
                                                                       self.start_time.strftime('%b %d %H:%M:%S'),
                                                                       datetime.datetime.now().strftime('%b %d %H:%M:%S'),
                                                                       estimated_time.strftime('%b %d %H:%M:%S')) % \
               (self.current, self.amax, (self.current / float(self.amax)) * 100)