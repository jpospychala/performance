#!/usr/bin/env python

import itertools
import json
import os
import requests
import sys
import time
import threading


def main(nodes):
    variants = get_variants(nodes[0])
    runner = Runner(variants)
    if len(runner.variants) == 0:
        print "nothing to do"
        return
    print "about to execute {0} variants across {1} nodes".format(len(runner.variants), len(nodes))

    threads = []
    for node in nodes:
        thread = HostRunner(node, runner)
        thread.start()
        threads.append(thread)
    while len(threads) > 0:
        time.sleep(1)
        runner.variants_status()
        for thread in threads:
            if thread.is_alive():
                thread.status()
            else:
                thread.join()
                threads.remove(thread)
        runner.save()




class Runner:
    def __init__(self, variants):
        self.isDirty = False
        self.reportpath = 'results/index.json'
        try:
          with open(self.reportpath, 'r') as f:
            self.report = json.load(f)
        except:
          self.report = []
        missing_variants = self.extract_missing_only(variants)
        self.variants = [{'status':'Todo', 'v':v} for v in missing_variants]


    def extract_missing_only(self, variants):
        missing_variants = []
        for v in variants:
            is_missing = True
            for r in self.report:
                if matches(v, r['params']):
                    is_missing = False
                    break
            if is_missing:
                missing_variants.append(v)
        return missing_variants

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
        statusgroups = [list(j) for (i, j) in itertools.groupby(statuses)]
        statusStr = ', '.join(['{0}: {1}'.format(j[0], len(j)) for j in statusgroups])
        print statusStr


class HostRunner(threading.Thread):

    def __init__(self, node, runner):
        threading.Thread.__init__(self)
        self.node = node
        self.runner = runner


    def status(self):
        pass


    def run(self):
        v = self.chooseVariant()
        while v:
            self.runAndFetch(v)
            v = self.chooseVariant()


    def chooseVariant(self):
        for v in self.runner.variants:
            if v['status'] == 'Todo':
                v['runner'] = self.node
        for toRun in self.runner.variants:
            if toRun['runner'] == self.node:
                toRun['status'] = 'Running'
                return toRun
        return None


    def runAndFetch(self, v):
        v['runner'] = None
        print "{0}: running {1} {2}".format(self.node, v['v'], v.get('retries'))
        ret = run_variant(self.node, v['v'])
        if 'error' in ret:
            print "{0}: failed {1}: {2}".format(self.node, v['v'], ret['error'])
            v['retries'] = v.get('retries', 0) + 1
            if v['retries'] > 5:
                v['status'] = 'Failed'
            else:
                v['status'] = 'Todo'
        else:
            for task in ret['result']:
                get_log(self.node, task['id'], task['params']['task'])
            self.runner.add_to_index(ret['result'])
            v['status'] = 'Done'


def get_variants(addr):
    return requests.get('http://{0}/variants'.format(addr)).json()

def get_log(addr, id, task):
    logdir = 'results/{0}'.format(id)
    if not os.path.exists(logdir):
      os.makedirs(logdir)
    with open('{0}/{1}.log'.format(logdir, task), 'w') as f:
        f.write(requests.get('http://{0}/log/{1}/{2}'.format(addr, id, task)).text)

def run_variant(addr, v):
    data = json.dumps(v)
    headers = {
        'Content-Type': 'application/json'
    }
    return requests.post('http://{0}/run'.format(addr), headers=headers, data=data).json()


def matches(v, r):
    '''True if all v properties equal r properties'''
    for key, val in v.items():
        if r.get(key, None) != val:
            return False
    return True

if __name__ == "__main__":
    main(sys.argv[1:])
