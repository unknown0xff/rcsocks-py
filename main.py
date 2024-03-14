#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import http_server
import json
import time
import threading
import subprocess
import random
import signal
import requests

local_ip = '127.0.0.1'

ping_interval = 15
ping_timeout = 15

devices_kv = {}
ssocks_kv = {}

used_port_list = []
running_process = []

# lock = threading.Lock()
exit_event = threading.Event()


def now():
    return int(time.time())


def get_available_port():
    while True:
        port = random.randint(10000, 30000)
        if port in used_port_list:
            continue
        else:
            used_port_list.append(port)
            break
    return port


def on_rcsocks(s5port, rport):
    cmd = 'ssocks/build/rcsocks --listen {} --port {}'.format(s5port, rport)
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_ssocks(name):
    s5port = get_available_port()
    rport = get_available_port()

    #t = threading.Thread(target=on_rcsocks, args=(socks5_port, rport))
    #t.start()
    #running_thread.append(t)

    p = on_rcsocks(s5port, rport)
    running_process.append(p)

    ssocks_kv[name] = {
        'p': p,
        's5port': s5port,
        'rport': rport,
    }
    return s5port, rport
    
   
def test():
    s5port, rport = run_ssocks('test')
    print("socks5:", s5port, "rport:", rport)
    #for p in running_process:
    #    rv = p.wait()
    #    print(rv)


def on_remove(name):
    if name in ssocks_kv:
        print('Remove:', name)
        p = ssocks_kv[name]['p']
        p.terminate()

        used_port_list.remove(devices_kv[name]['s5port'])
        used_port_list.remove(devices_kv[name]['rport'])

        del ssocks_kv[name]
        del devices_kv[name]


def on_timeout():
    while not exit_event.is_set():
        exit_event.wait(ping_timeout)

        copy_devices = devices_kv.copy()

        for k, v in copy_devices.items():
            if now() - v['time'] > ping_interval + ping_timeout:
                on_remove(k)


@http_server.get('/')
def hello(http, data):
    return 'hello.'


@http_server.post('/device/set_config')
def set_config(http, data):
    global ping_interval, ping_timeout
    ping_interval = data['ping_interval']
    ping_timeout = data['ping_timeout']
    return "OK"


@http_server.get('/device/get_config')
def get_config(http, data):
    d = {
        'ping_interval': ping_interval,
        'ping_timeout': ping_timeout,
    }
    return d

@http_server.post('/device/register')
def register(http, data):
    data = json.loads(data)
    device_name = data['device_name']

    if device_name in devices_kv:
        on_remove(device_name)

    s5port, rport = run_ssocks(device_name)

    devices_kv[device_name] = {
        'device_id': data['device_id'],
        'client_ip': data['ip'],
        'region': data['region'],
        'city': data['city'],
        'country': data['country'],
        'socks5': '{}:{}'.format(local_ip, s5port),
        's5port': s5port,
        'rport': rport,
        'time': now(),
    }

    response = {
        'rport': rport,
    }
    return response


@http_server.post('/device/ping')
def ping(http, data):
    data = json.loads(data)
    device_name = data['device_name']

    if device_name in devices_kv:
        devices_kv[device_name]['time'] = now()
        return "OK"

    return "FAILED"


@http_server.get('/api/get_device_list')
def get_device_list(http, data):
    return devices_kv


req = requests.get('https://ipinfo.io/json')
data = req.json()
local_ip = data['ip']

running_thread = [
    threading.Thread(target=on_timeout)
]

def signal_handler(sig, frame):
    print('Exiting...')
    exit_event.set()
    map(lambda p: p.terminate(), running_process)
    map(lambda t: t.join(), running_thread)
    sys.exit(0)


signal.signal(signal.SIGINT, lambda x, y: signal_handler(x, y))
# signal.signal(signal.SIGTERM, signal_handler)

for t in running_thread:
    t.start()

# test()
http_server.run()
