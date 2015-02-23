#!/usr/bin/env python

import itertools
import json
import requests
import sys
import time
import threading

class HostRunner(threading.Thread):

    def __init__(self, node, variants):
        threading.Thread.__init__(self)
        self.node = node
        self.variants = variants


    def status(self):
        pass


    def run(self):
        for v in self.variants:
            if v['status'] == 'Todo':
                v['runner'] = self.node
        for v in self.variants:
            if v['runner'] == self.node:
                v['status'] = 'Running'
                print "{0}: running".format(v)
                run_variant(self.node, v['v'])
                v['status'] = 'Done'


def get_variants(addr):
    return requests.get('http://{0}/variants'.format(addr)).json()

def run_variant(addr, v):
    data = json.dumps(v)
    headers = {
        'Content-Type': 'application/json'
    }
    return requests.post('http://{0}/run'.format(addr), headers=headers, data=data).json()

def variants_status(variants):
    statuses = [v['status'] for v in variants]
    statusgroups = [list(j) for (i, j) in itertools.groupby(statuses)]
    statusStr = ', '.join(['{0}: {1}'.format(j[0], len(j)) for j in statusgroups])
    print statusStr


def main(nodes):
    variants = [{'status':'Todo', 'v':v} for v in get_variants(nodes[0])]
    print "about to execute {0} variants across {1} nodes".format(len(variants), len(nodes))

    # calculate TODO list
    threads = []
    for node in nodes:
        thread = HostRunner(node, variants)
        thread.start()
        threads.append(thread)
    while len(threads) > 0:
        time.sleep(1)
        variants_status(variants)
        for thread in threads:
            if thread.is_alive():
                thread.status()
            else:
                thread.join()
                threads.remove(thread)


if __name__ == "__main__":
    main(sys.argv[1:])
