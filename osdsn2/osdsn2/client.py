import socket
import time
import logging
import datetime
import statistics

HOST = '127.0.0.1'
PORT = 20000
SOCKET = None

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')

LOG = logging.getLogger("client")


def connect():
    global SOCKET
    SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SOCKET.connect((HOST, PORT))


def disconnect():
    SOCKET.close()


def _send_cmd(command):
    SOCKET.send((command + '\n').encode())
    str_builder = ""
    while True:
        part = SOCKET.recv(64)
        if not part:
            break
        decoded = part.decode('ISO-8859-1')
        str_builder += decoded
        if 'SERVER_COMPLETED' in str_builder:
            break
        print(decoded, end='')
    print('Success on executing command "', command, '"')
    print('Waiting to proceed now.')
    time.sleep(5)
    return str_builder


def stack():
    _send_cmd('s')


def unstack():
    _send_cmd('u')


def quit():
    _send_cmd('q')


def start_log_sys():
    _send_cmd('a')


def stop_log_sys():
    _send_cmd('b')


def incr_range_from():
    _send_cmd('d')


def get_range_from():
    return int(_send_cmd('c'))


if __name__ == '__main__':
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, handlers=[
        logging.StreamHandler(),
        logging.FileHandler('client.log', mode='a')
    ])
    LOG.info('Experiment Begin.')
    # This is an experiment
    connect()
    global_sample = []
    stack_sample = []
    unstack_sample = []
    for i in range(1, 100):
        global_now = datetime.datetime.now()
        stack_now = datetime.datetime.now()
        stack()
        stack_later = datetime.datetime.now()
        unstack_now = datetime.datetime.now()
        unstack()
        unstack_later = datetime.datetime.now()
        global_later = datetime.datetime.now()
        global_sample.append((global_later - global_now).total_seconds())
        stack_sample.append((stack_later - stack_now).total_seconds())
        unstack_sample.append((unstack_later - unstack_now).total_seconds())
        LOG.info('Global=%d, Stack=%d, Unstack=%d' % (global_sample[len(global_sample) - 1],
                                                      stack_sample[len(stack_sample) - 1],
                                                      unstack_sample[len(unstack_sample) - 1]))

    disconnect()
    LOG.info('Global Mean=%s, Global Std=%s' % (statistics.mean(global_sample), statistics.stdev(global_sample)))
    LOG.info('Stack Mean=%s, Stack Std=%s' % (statistics.mean(stack_sample), statistics.stdev(stack_sample)))
    LOG.info('Unstack Mean=%s, Unstack Std=%s' % (statistics.mean(unstack_sample), statistics.stdev(unstack_sample)))
    LOG.info('Experiment End.')
