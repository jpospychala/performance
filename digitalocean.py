#!/usr/bin/env python

import datetime
import json
import os
import random
import requests
import shutil
import signal
import socket
import subprocess
import sys
import time

def main(args):
    cmd = args.pop(0)
    if cmd == "status":
        status(args[0])
    elif cmd == "stop":
        stop(args[0])
    elif cmd == "ssh":
        ssh(args[0])
    else:
        print "unknown command {0}".format(cmd)


class DigitalOceanDroplet:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.label = 'digitalocean{0}'.format(self.size)

    def create(self):
        self.d = get_or_create(self.name, self.size)
        if not self.d:
            self.d = wait_for_droplet(self.name)
        port = 9081
        self.addr = "{0}:{1}".format(self.d.ip, port)
        provision(self.d)
        wait_for_port(self.d.ip, port)
        print "provisioned {0}".format(self.name)

    def destroy(self):
        stop_droplet(self.d)


def get_or_create(dropletName, dropletSize):
    d = get_droplet(dropletName)
    if d:
        return d
    print "{0} not found. Creating...".format(dropletName)
    create_droplet(dropletName, dropletSize)


def wait_for_droplet(dropletName):
    d = None
    start = time.time()
    while not d:
        d = get_droplet(dropletName)
        time.sleep(10)
    wait_for_port(d.ip, 22)

    secs = time.time() - start
    print "reached {0} after {1} secs".format(dropletName, secs)
    return d


def provision(d):
    subprocess.call(["rsync", "-ace", "ssh -q -oStrictHostKeyChecking=no", "./run.sh", "root@{0}:/root".format(d.ip)])
    subprocess.call(["ssh", "-q", "-oStrictHostKeyChecking=no", "root@{0}".format(d.ip),"bash /root/run.sh"])

def status(dropletName):
    d = get_droplet(dropletName)
    assert_droplet(d, dropletName)
    print "IP: {0} ID: {1}".format(d.ip, d.id)


def stop(dropletName):
    d = get_droplet(dropletName)
    assert_droplet(d, dropletName)
    stop_droplet(d)


def ssh(dropletName):
    d = get_droplet(dropletName)
    assert_droplet(d, dropletName)
    subprocess.call(["ssh", "-oStrictHostKeyChecking=no", "root@{0}".format(d.ip)])


def assert_droplet(d, dropletName):
    if not d:
        print "Droplet {0} not found".format(dropletName)
        exit(1)


class Droplet:
    pass


def stop_droplet(d):
    r = do_request('DELETE', "droplets/{0}".format(d.id))
    if r.status_code != 204:
        raise RuntimeError(r.text)


def get_droplet(dropletName):
    r = do_request("GET", "droplets")
    if r.status_code != 200:
        raise RuntimeError(r.text)
    droplets = r.json().get("droplets", {})
    for droplet in droplets:
        if droplet.get("name") == dropletName:
            d = Droplet()
            net = droplet["networks"]["v4"]
            if len(net) == 0:
                return False
            d.ip = net[0]["ip_address"]
            d.id = droplet["id"]
            d.name = dropletName
            return d
    return False


def get_sshkeys():
    r = do_request("GET", "account/keys")
    if r.status_code != 200:
        raise RuntimeError(r.text)
    return [key["fingerprint"] for key in r.json().get("ssh_keys", [])]


def create_droplet(dropletName, dropletSize):
    sshKeys = get_sshkeys()
    payload = {
        "name":dropletName,
        "region":"nyc3",
        "size":dropletSize,
        "image":"ubuntu-14-04-x64",
        "ssh_keys":sshKeys
    }
    r = do_request("POST", "droplets", data=payload)
    if r.status_code != 202:
        print r.status_code
        raise RuntimeError(r.text)


def do_request(method, path, data=None):
    if "DOTOKEN" not in os.environ:
        raise RuntimeError("Error: Variable $DOTOKEN with digitalocean API token is not set.")

    headers = {
        "Authorization": "Bearer {0}".format(os.environ['DOTOKEN']),
        "Content-Type": "application/json"
    }
    url = "https://api.digitalocean.com/v2/{0}".format(path)
    if data:
        data = json.dumps(data)
    ret = requests.request(method, url, headers=headers, data=data)
    rateLimit = int(ret.headers['RateLimit-Limit'])
    rateRemaining = int(ret.headers['RateLimit-Remaining'])
    rateLimitReset = datetime.datetime.fromtimestamp(int(ret.headers['RateLimit-Reset']))
    if (rateRemaining*1.0 / rateLimit) < 0.3:
        print "digitalocean rate limit ({0}/{1}) reset: {2}".format(rateRemaining, rateLimit, rateLimitReset)
    return ret


def wait_for_port(host, port):
    port_is_open = False
    while not port_is_open:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host,port))
        port_is_open = result == 0
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: {0} cmd".format(sys.argv[0])
    else:
        main(sys.argv[1:])
