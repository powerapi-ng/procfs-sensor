# MIT License

# Copyright (c) 2021 PowerAPI

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import subprocess
import json
from datetime import datetime
import sys
import socket
import threading


def read_config(config_file):
    """ Read the config from the config_files specified in argument"""
    file_object = open(config_file, "r")
    json_content = file_object.read()
    file_object.close()
    return json.loads(json_content)


def mesure_cpu_usage():
    """Mesure the cpu usage of process using pidstat"""
    timestamp = datetime.today()
    raw_stat = str(subprocess.check_output(["pidstat"]))

    stat = raw_stat.split('\\n')
    pid_cpu_usage = {}
    for i in range(3, len(stat)):
        pid_stat = stat[i].split(' ')

        pid_stat = list(filter(('').__ne__, pid_stat))
        if len(pid_stat) != 10:
            continue

        pid_cpu_usage[pid_stat[2]] = pid_stat[7]

    return timestamp, pid_cpu_usage


def send_tcp_report(sock, report):
    """ Send the json report using TCP"""

    to_send = report.encode('utf-8')
    sock.sendall(to_send)


def send_report(sock, report):
    """ Send the json report using the output method specified in the config"""

    send_tcp_report(sock, report)


def sensor_mesure_send(sampling_interval, sensor, target, sock):
    """ Produce the report from scratch and send it"""
    probe = threading.Timer(sampling_interval / 1000, sensor_mesure_send, [sampling_interval, sensor, target, sock])
    probe.start()

    timestamp, pid_cpu_usage = mesure_cpu_usage()

    cgroup_cpu_usage = {}
    global_cpu_usage = 0

    for process in pid_cpu_usage:
        global_cpu_usage += float(pid_cpu_usage[process].replace(", ", "."))

    for cgroup in target:
        cgroup_cpu_usage[cgroup] = 0
        cgroup_pid_file = open('/sys/fs/cgroup/perf_event/' + cgroup + '/tasks', "r")
        cgroup_pid_raw = cgroup_pid_file.read()
        cgroup_pid_file.close()
        pid_list = cgroup_pid_raw.split('\n')

        for process in pid_list:
            if process not in pid_cpu_usage.keys():
                continue
            cgroup_cpu_usage[cgroup] += float(pid_cpu_usage[process].replace(", ", "."))

    tmstp_tmp = str(timestamp)
    tmstp = tmstp_tmp[:tmstp_tmp.index(' ')] + 'T' + tmstp_tmp[tmstp_tmp.index(' ') + 1:]  # Convert to mongo timestamp format
    report = {'timestamp': tmstp, 'sensor': str(sensor), 'target': target, 'usage': cgroup_cpu_usage, "global_cpu_usage": global_cpu_usage}
    report_json = json.dumps(report)
    send_report(sock, report_json)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Precise config file name: ")
        file_name = input()
    else:
        file_name = sys.argv[1]

    if len(file_name) < 5:
        logging.error("Error: the config file must be a .json")
    if file_name[-5:] != '.json':
        logging.error("Error: the config file must be a .json")

    config = read_config(file_name)

    sensor = config['name']
    target = config['target']
    sampling_interval = int(config['sampling-interval'])

    output = config['output']

    logging.basicConfig(level=logging.WARNING if config['verbose'] else logging.INFO)
    logging.captureWarnings(True)

    host, port = output['uri'], output['port']
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    sensor_mesure_send(sampling_interval, sensor, target, sock)
