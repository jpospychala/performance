#!/usr/bin/env python

import json
import os
import random
import requests
import shutil
import socket
import subprocess
import sys
import time
import runner

def main(args):
    cmd = args.pop(0)
    if cmd == "status":
        status(args[0])
    elif cmd == "stop":
        stop(args[0])
    elif cmd == "ssh":
        ssh(args[0])
    elif cmd == "run":
        run(*args)
    elif cmd == "parallel":
        parallel(10, "512mb")
    else:
        print "unknown command {0}".format(cmd)

def parallel(dropletsCount, dropletSize):
    dropletsList = []
    for i in range(dropletsCount):
        get_or_create('droplet{0}'.format(i), dropletSize)
    for i in range(dropletsCount):
        d = wait_for_droplet('droplet{0}'.format(i))
        dropletsList.append(d)
    provisionThreads = []
    for d in dropletsList:
        t = provision(d)
        provisionThreads.append(t)
    for t in provisionThreads:
        t.wait()
    print "provisioned all threads"
    ipList = ['{0}:9081'.format(d.ip) for d in dropletsList]
    runner.main(dropletSize, ipList)


def get_or_create(dropletName, dropletSize):
    d = get_droplet(dropletName)
    if not d:
        print "Droplet {0} not found. Creating...".format(dropletName)
        create_droplet(dropletName, dropletSize)


def wait_for_droplet(dropletName):
    d = None
    while not d:
        d = get_droplet(dropletName)
    secs = wait_for_port(d.ip, 22)
    if secs > 5:
        print "reached {0} after {1} secs".format(dropletName, secs)
    return d


def provision(d):
    print "provision {0}".format(d.ip)
    subprocess.call(["rsync", "-ace", "ssh -q -oStrictHostKeyChecking=no", "./run.sh", "root@{0}:/root".format(d.ip)])
    t = subprocess.Popen(["ssh", "-q", "-oStrictHostKeyChecking=no", "root@{0}".format(d.ip),"bash /root/run.sh"])
    return t

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
        raise RuntimeError(r.json())
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
    headers = {
        "Authorization": "Bearer {0}".format(os.environ['DOTOKEN']),
        "Content-Type": "application/json"
    }
    url = "https://api.digitalocean.com/v2/{0}".format(path)
    if data:
        data = json.dumps(data)
    return requests.request(method, url, headers=headers, data=data)


def wait_for_port(host, port):
    start = time.clock()
    port_is_open = False
    while not port_is_open:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host,port))
        port_is_open = result == 0
        time.sleep(1)
    after = time.clock()
    return after-start


if __name__ == "__main__":
    if "DOTOKEN" not in os.environ:
        print "Error: Variable $DOTOKEN with digitalocean API token is not set."
        exit(1)

    if len(sys.argv) < 2:
        print "Usage: {0} cmd".format(sys.argv[0])
    else:
        main(sys.argv[1:])
