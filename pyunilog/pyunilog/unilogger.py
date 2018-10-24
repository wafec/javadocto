import threading
import time
import re
import datetime
import argparse
import sys


class FileMonitor:
    INTERVAL = 0.1

    def __init__(self, file_path):
        self.subscribers = []
        self.file_path = file_path
        self.t = None
        self._stop = False

    def start_reading(self):
        if self.t:
            return
        self.t = threading.Thread(target=self._worker)
        self.t.start()

    def stop_reading(self):
        if not self.t:
            return
        self._stop = True

    def _update(self,line):
        for subscriber in self.subscribers:
            subscriber.update(line)

    def _worker(self):
        with open(self.file_path, 'r') as istream:
            line = istream.readline()
            while True:
                if line:
                    self._update(line)
                line = istream.readline()
                if self._stop:
                    break
                if not line:
                    time.sleep(self.INTERVAL)
        self._stop = False


class UniLogger:
    INTERVAL = 0.5

    def __init__(self, files, ignore_list, ends_with=None, full=False):
        self.files = files
        self.ignore_list = ignore_list
        self.ends_with = ends_with
        self.full = full
        self.file_monitors = []
        self.buffer = []
        self.t = threading.Thread(target=self._worker)
        self.lock = threading.Lock()
        self._stop = False
        self.start_time = datetime.datetime.now()
        self.t.start()
        self.active = True

    def initialize(self):
        for file_path in self.files:
            file_monitor = FileMonitor(file_path)
            file_monitor.subscribers.append(self)
            self.file_monitors.append(file_monitor)
            file_monitor.start_reading()

    def close(self):
        if not self.active:
            return
        for file_monitor in self.file_monitors:
            file_monitor.stop_reading()
            file_monitor.subscribers.remove(self)
        self.file_monitors = []
        self._stop = True
        self.active = False

    def update(self, line):
        self.lock.acquire()
        try:
            self.buffer.append(line)
        finally:
            self.lock.release()
        self._check_stop_condition(line)

    def _check_stop_condition(self, line):
        if not self.ends_with:
            return
        m = re.match(self.ends_with, line)
        if m:
            self.close()

    def _worker(self):
        while True:
            if self._stop:
                break
            self._take_buffer()
            time.sleep(self.INTERVAL)
        self._take_buffer()

    def _take_buffer(self):
        mapping = []
        self.lock.acquire()
        try:
            for line in self.buffer:
                dt = self._get_datetime_from_line(line)
                if not dt:
                    continue
                mapping.append((dt, line))
            mapping = sorted(mapping, key=lambda item: item[0])
            self.buffer = []
        finally:
            self.lock.release()
        for item in mapping:
            if not self.full and item[0] < self.start_time:
                continue
            logger_name = self._get_logger_name(item[1])
            if self._check_ignore_list(logger_name):
                continue
            print(item[1], end='', flush=True)

    def _check_ignore_list(self, item):
        if not item:
            return False
        for ignore_item in self.ignore_list:
            if item.startswith(ignore_item):
                return True
        return False

    def _get_datetime_from_line(self, line):
        dt = self._get_datetime_from_sys_line(line)
        if not dt:
            dt = self._get_datetime_from_test_manager_line(line)

        return dt

    def _get_datetime_from_sys_line(self, line):
        m = re.match("^([a-zA-Z]+\s\d{2}\s\d{2}:\d{2}:\d{2}).*", line)
        if m:
            res = m.group(1)
            return datetime.datetime.strptime(res, "%b %d %X").replace(year=datetime.datetime.now().year)
        return None

    def _get_datetime_from_test_manager_line(self, line):
        m = re.match("^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})", line)
        if m:
            res = m.group(0)
            return datetime.datetime.strptime(res, "%Y-%m-%d %H:%M:%S")
        return None

    def __del__(self):
        self._stop = True

    def _get_logger_name(self, line):
        logger_name = self._get_logger_name_from_sys_line(line)
        if not logger_name:
            logger_name = self._get_logger_name_from_test_manager_line(line)
        return logger_name

    def _get_logger_name_from_sys_line(self, line):
        m = re.match("^.+\s\d+\s\d+:\d+:\d+\s.+\d(.+)\[", line)
        if m:
            res = m.group(1)
            return res
        return None

    def _get_logger_name_from_test_manager_line(self, line):
        m = re.match("^\d+-\d+-\d+\s\d+:\d+:\d+,\d+\s.+\s\[(.+)\]", line)
        if m:
            res = m.group(1)
            return res
        return None


if __name__ == "__main__":
    def main_unilogger(args):
        ignore_list = args.ignore if args.ignore else []
        unilogger = UniLogger(args.files, ignore_list, args.stop, args.full)
        try:
            unilogger.initialize()
            while unilogger.active:
                time.sleep(1)
        finally:
            unilogger.close()

    parser = argparse.ArgumentParser("unilogger")
    parser.add_argument("--files", type=str, nargs='+', required=True)
    parser.add_argument("--ignore", type=str, nargs='+', required=False, default=None)
    parser.add_argument("--stop", type=str, required=False, default=None)
    parser.add_argument("--full", required=False, default=False, action="store_true")
    parser.set_defaults(f=main_unilogger)

    args = parser.parse_args()
    args.f(args)
