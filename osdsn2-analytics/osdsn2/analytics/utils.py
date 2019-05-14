import logging
import datetime


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