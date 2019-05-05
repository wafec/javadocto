import re
import datetime
import os
import argparse
import time


class TimeBuffer(object):
    def __init__(self, t_now, line):
        self.t_now = t_now
        self.line = line


def sort_log_file(path, year):
    buffer_time = None
    buffer = []
    time_1_pattern = r'^\w+\s+(?P<date>\d+-\d+-\d+\s?\d+:\d+:\d+,\d+)\s'
    time_2_pattern = r'^(?P<date>\w+\s+\d+\s+\d+:\d+:\d+)\s'
    dest_path = path + '.tmp'
    print('Sorting', path)
    bytes_n = 0
    bytes_total = os.path.getsize(path)
    errors = 0
    with open(path, 'r', encoding='iso-8859-1') as r, open(dest_path, 'w', encoding='iso-8859-1') as w:
        line = r.readline()
        while line:
            bytes_n += len(line.encode('iso-8859-1'))
            progress = (bytes_n * 100) / bytes_total
            print('\rRead %010d / %010d %3d E=%04d' % (bytes_n, bytes_total, progress, errors) + '%', end='')
            try:
                if line.strip():
                    original_line = line
                    line = line.replace('  ', ' ').replace('   ', ' ')
                    m = re.match(time_1_pattern, line)
                    t_now = None
                    if m:
                        t_now = datetime.datetime.strptime(m.group('date'), '%Y-%m-%d %H:%M:%S,%f')
                        t_now = datetime.datetime(t_now.year, t_now.month, t_now.day, t_now.hour, t_now.minute,
                                                  t_now.second, 0)
                    else:
                        m = re.match(time_2_pattern, line)
                        if m:
                            t_now = datetime.datetime.strptime(m.group('date'), '%b %d %H:%M:%S')
                            t_now = datetime.datetime(year, t_now.month, t_now.day, t_now.hour, t_now.minute, t_now.second,
                                                      100)
                        else:
                            # print('Neither time pattern 1 nor 2 have matched.')
                            pass
                    if t_now:
                        t_buffer = datetime.datetime(t_now.year, t_now.month, t_now.day, t_now.hour)
                        if buffer_time is None:
                            buffer_time = t_buffer
                        if t_buffer == buffer_time:
                            buffer.append(TimeBuffer(t_now, original_line))
                        else:
                            for time_buffer in sorted(buffer, key=lambda x: x.t_now):
                                w.write(time_buffer.line)
                                w.flush()
                            # print('Time saved for', buffer_time.strftime('%Y-%m-%d %H:%M'))
                            buffer_time = t_buffer
                            buffer.clear()
                            buffer.append(TimeBuffer(t_now, original_line))
                    else:
                        # print('Cannot parse line', original_line[:30], '... of length', len(original_line.strip()))
                        # print('Warning.', 't_now cannot be None.')
                        if len(buffer) > 0:
                            t_aux = buffer[len(buffer) - 1].t_now
                        else:
                            t_aux = buffer_time
                        buffer.append(TimeBuffer(t_aux, original_line))
                else:
                    # print('Blank line skipped.')
                    pass
            except Exception as exc:
                # print('Error.', exc)
                errors ++ 1
            finally:
                line = r.readline()
        if len(buffer) > 0:
            for time_buffer in sorted(buffer, key=lambda x: x.t_now):
                w.write(time_buffer.line)
                w.flush()
        print('\rRead %10d / %10d %3d' % (bytes_total, bytes_total, 100) + '%', end='\n')
    os.remove(path)
    os.rename(dest_path, path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('ext')
    parser.add_argument('year', type=int)

    args = parser.parse_args()
    path = args.path
    ext = args.ext
    year = args.year
    print('You enter with path', path, 'and ext', ext)
    paths = []
    if os.path.isdir(path):
        print('Your path', path, 'is a dir')
        paths = [path + '/' + x for x in os.listdir(path) if os.path.isfile(path + '/' + x) and (ext == 'any' or
                                                                                                 x.endswith(ext))
                 and not x.endswith('.tmp')]
        print('There were found', len(paths), 'there that ends with', ext)
    else:
        if ext != 'any' and not path.endswith(ext):
            raise ValueError('path needs to end as ext parameter')
        paths.append(path)
    for x in paths:
        sort_log_file(x, year)
