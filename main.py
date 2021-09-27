# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
    timestamp=datetime.today()
    raw_stat = str(subprocess.check_output(["pidstat"]))

    stat = raw_stat.split('\\n')
    pid_cpu_usage = {}
    for i in range(3,len(stat)) :
        pid_stat = stat[i].split(' ')

        pid_stat = list(filter(('').__ne__, pid_stat))
        if len(pid_stat) != 10 :
            continue

        pid_cpu_usage[pid_stat[2]] = pid_stat[7]

    return timestamp, pid_cpu_usage


def send_tcp_report(sock ,report):
    """ Send the json report using TCP"""


    to_send = report.encode('utf-8')
    sock.sendall(to_send)


def send_report(sock,report):
    """ Send the json report using the output method specified in the config"""

    send_tcp_report(sock,report)


def sensor_mesure_send(frequency,sensor,target,sock):
    """ Produce the report from scratch and send it"""
    probe = threading.Timer(frequency/1000,sensor_mesure_send,[frequency,sensor,target,sock])
    probe.start()

    timestamp, pid_cpu_usage = mesure_cpu_usage()

    cgroup_cpu_usage = {}
    global_cpu_usage = 0

    for process in pid_cpu_usage.keys():
        global_cpu_usage += float(pid_cpu_usage[process].replace(",","."))



    for cgroup in target :
        cgroup_cpu_usage[cgroup] = 0
        cgroup_pid_file = open('/sys/fs/cgroup/perf_event/' + cgroup + '/tasks', "r")
        cgroup_pid_raw =cgroup_pid_file.read()
        cgroup_pid_file.close()
        pid_list = cgroup_pid_raw.split('\n')

        for process in pid_list:
            if process not in pid_cpu_usage.keys():
                continue
            cgroup_cpu_usage[cgroup] += float(pid_cpu_usage[process].replace(",","."))

    tmstp = str(timestamp)
    tmstp[tmstp.index(' ')] = 'T' # Convert to mongo timestamp format
    report = {'timestamp':tmstp, 'sensor':str(sensor), 'target':target, 'usage':cgroup_cpu_usage, "global_cpu_usage":global_cpu_usage}
    report_json = json.dumps(report)
    send_report(sock,report_json)


def main():
    """Initialize the sensor and run it core function at the frequency required by the config"""


    if len(sys.argv) == 0 :
        print("Precise config file name : ")
        file_name = input()
    else:
        file_name = sys.argv[1]

    if len(file_name) < 5 :
        logging.error("Error : the config file must be a .json")
    if file_name[-5:] != '.json':
        logging.error("Error : the config file must be a .json")

    config = read_config(file_name)

    sensor=config['name']
    target=config['target']
    frequency = int(config['frequency'])

    output = config['output']

    logging.basicConfig(level=logging.WARNING if config['verbose'] else logging.INFO)
    logging.captureWarnings(True)

    host, port = output['uri'], output['port']
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    sensor_mesure_send(frequency, sensor,target,sock)


main()
