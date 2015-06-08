#!/usr/bin/env python

import simplejson
import datetime
import digitalocean
import itertools
import json
import os
import requests
import signal
import sys
import time
import threading


def main(nodes):
    runner = Runner()
    threads = []
    firstNode = nodes[0]
    for node in nodes:
        # TODO master should be the first up, not the first on list
        thread = HostRunner(node, runner, node == firstNode)
        thread.start()
        threads.append(thread)
    while len(threads) > 0:
        time.sleep(30)
        runner.variants_status()
        for thread in threads:
            if thread.is_alive():
                thread.status()
            else:
                thread.join()
                threads.remove(thread)
        runner.save()


class LocalNode:
    def __init__(self, name):
        self.name = name
        self.label = name
        self.addr = "localhost:9081"

    def create(self):
        pass

    def destroy(self):
        pass


class Runner:
    def __init__(self):
        self.variants = []
        self.ready = False
        self.startTime = datetime.datetime.now()
        self.isDirty = False
        self.reportpath = 'results/index.json'
        try:
          with open(self.reportpath, 'r') as f:
            self.report = json.load(f)
        except:
          self.report = []

    def set_variants(self, variants):
        missing_variants = self.extract_missing_only(variants)
        new_variants = [{'status':'Todo', 'v':v} for v in missing_variants]

        if len(new_variants) > 0:
            print "about to execute {0} variants".format(len(new_variants))
        else:
            print "nothing to do"

        self.variants = new_variants
        self.ready = True

    def extract_missing_only(self, variants):
        start = time.time()
        missing = []

        lastKeys = None
        lastKeysHash = None
        reportFilteredKeys = []
        for v in variants:
            keysHash = id(sorted(v.keys()))
            if keysHash != lastKeysHash:
                lastKeys = sorted(v.keys())
                lastKeysHash = keysHash
                reportFilteredKeys = set([self.vid({ k: r['params'].get(k, None) for k in lastKeys }) for r in self.report])

            if not self.vid(v) in reportFilteredKeys:
                missing.append(v)
        return missing

    def vid(self, obj):
        return json.dumps(obj, sort_keys=True)


    def add_to_index(self, entries):
        self.report.extend(entries)
        self.isDirty = True


    def save(self):
        if not self.isDirty:
            return
        with open(self.reportpath, 'w') as f:
            json.dump(self.report, f)
        self.isDirty = False


    def variants_status(self):
        statuses = [v['status'] for v in self.variants]
        statuses.sort()
        statusgroups = [list(j) for (i, j) in itertools.groupby(statuses)]
        statusesDict = dict([[j[0], len(j)] for j in statusgroups])
        statusStr = ', '.join(['{0}: {1}'.format(j[0], len(j)) for j in statusgroups])
        now = datetime.datetime.now()
        timePassed = now - self.startTime
        eta = timePassed * statusesDict.get('Todo', 0)/statusesDict.get('Done', 1)
        print "{0}: {1} ETA {2}".format(now, statusStr, str(eta))


class HostRunner(threading.Thread):

    def __init__(self, node, runner, is_master):
        threading.Thread.__init__(self)
        self.node = node
        self.runner = runner
        self.is_master = is_master


    def status(self):
        pass


    def run(self):

        self.node.create()
        set_name(self.node.addr, self.node.label)
        self.do_master_tasks()
        while not self.runner.ready:
            time.sleep(1)
        v = self.chooseVariant()
        while v:
            try:
                self.runAndFetch(v)
            except requests.exceptions.ConnectionError:
                print "{0}: Connection error, recreating node".format(self.node.name)
                self.node.create()
                set_name(self.node.addr, self.node.label)
            v = self.chooseVariant()
        self.node.destroy()


    def do_master_tasks(self):
        if not self.is_master:
            return

        variants = get_variants(self.node.addr)
        self.runner.set_variants(variants)


    def chooseVariant(self):
        for v in self.runner.variants:
            if v['status'] == 'Todo':
                v['runner'] = self.node.name
        for toRun in self.runner.variants:
            if toRun['runner'] == self.node.name:
                toRun['status'] = 'Running'
                return toRun
        return None


    def runAndFetch(self, v):
        v['runner'] = None
        print "{0}: running {1} {2}".format(self.node.name, v['v'], v.get('retries'))
        ret = run_variant(self.node.addr, v['v'])
        if 'error' in ret:
            print "{0}: failed {1}: {2}".format(self.node.name, v['v'], ret['error'])
            get_log(self.node.addr, ret['id'], 'log')
            cat_log(ret['id'])
            v['retries'] = v.get('retries', 0) + 1
            if v['retries'] > 5:
                v['status'] = 'Failed'
            else:
                v['status'] = 'Todo'
        else:
            for task in ret['result']:
                get_log(self.node.addr, task['id'], task['task'])
            self.runner.add_to_index(ret['result'])
            v['status'] = 'Done'


def get_variants(addr):
    return requests.get('http://{0}/variants'.format(addr)).json()


def set_name(addr,name):
    data=json.dumps({'name': name})
    headers = {'Content-Type': 'application/json'}
    requests.post('http://{0}/name'.format(addr), headers=headers, data=data)


def cat_log(id):
    with open('results/{0}/log.log'.format(id), 'r') as f:
        for l in f:
            print 'log: ', l


def get_log(addr, id, task):
    logdir = 'results/{0}'.format(id)
    if not os.path.exists(logdir):
      os.makedirs(logdir)
    text = requests.get('http://{0}/log/{1}/{2}'.format(addr, id, task)).text
    with open('{0}/{1}.log'.format(logdir, task), 'w') as f:
        f.write(text)

def run_variant(addr, v):
    data = json.dumps(v)
    headers = {'Content-Type': 'application/json'}
    ret = requests.post('http://{0}/run'.format(addr), headers=headers, data=data)
    try:
        return ret.json()
    except simplejson.JSONDecodeError as e:
        raise e


def createNodes(argsstr):
    args = argsstr.split(':')
    count = 1
    if len(args) > 0:
        count = int(args[1])
    if args[0] == 'local':
        return [LocalNode('local{0}'.format(i)) for i in range(count)]
    elif args[0] == 'digitalocean':
        size = args[2]
        return [digitalocean.DigitalOceanDroplet('droplet{0}'.format(i), size) for i in range(count)]


def signal_handler(signal, frame):
    print "exit"
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "usage: ./runner.py type:count:detail\nexamples:\n ./runner.py local:1\n ./runner.pl digitalocean:3:512mb"
        sys.exit(1)
    nodes = createNodes(sys.argv[1])
    main(nodes)
