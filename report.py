#!/usr/bin/env python

import json
import sys
import os
import math
import functools
import numpy
import time

postProcess = [
    {
        "task": "sleep",
        "header": "latency (ms)",
        "fn": lambda row, count, cfg: int(row[0]) - int(cfg["params"]["time"])
    },
    {
        "task": "consumer",
        "product": "rabbitmq",
        "header": "throughput (ms)",
        "fn": lambda row, count, cfg: 0 if d[0]== 0 else math.round(count*1000/(d[0]))
    }
]

actualCoresCountMap =  {
    'digitalocean512mb': '1',
    'digitalocean2gb': '2',
    'digitalocean16gb': '8',
    'local0': '2'
}

def main(srcdir):
    try:
        with open('report/result.json', 'r') as f:
            report = json.load(f)
    except:
        report = []

    try:
        with open('{0}/index.json'.format(srcdir), 'r') as f:
            index = json.load(f)
    except:
        index = []
    reportHas = set(["{0}{1}".format(e['id'], e['task']) for e in report])

    i = 0
    for entry in index:
        i += 1
        sys.stderr.write('\b\b\b\b{:0>3d}%'.format(i*100/len(index)))

        if "{0}{1}".format(entry['id'], entry['task']) in reportHas:
            continue

        logPath = 'results/{0}/{1}.log'.format(entry["id"], entry["task"])
        try:
            headers, values = readLog(logPath)
        except BaseException as ex:
            sys.stderr.write("skipping {0} {1}\n".format(entry, ex))
            continue

        doContinue = False
        v_i = 0
        if entry["sysinfo"]["oslabel"] in actualCoresCountMap:
            entry["sysinfo"]["cpu cores"] = actualCoresCountMap[entry["sysinfo"]["oslabel"]]
        entry["stats"] = {}
        for v in values:
            if len(v) == 0:
                sys.stderr.write("skipping/no values {0}\n".format(entry))
                doContinue = True
                break
            dimension = headers[v_i]
            entry["stats"][dimension] = calculateStats(v)
        if doContinue:
            continue
        for pp in postProcess:
            if pp["task"] == entry["task"]:
                vByCols = colsByRowsToRowsByCols(values)
                pp_v = [pp["fn"](d, len(vByCols), entry) for d in vByCols]
                dimension = pp["header"]
                entry["stats"][dimension] = calculateStats(pp_v)
        report.append(entry)

        if (i % 100) == 0:
            with open('report/result.json', 'w') as f:
                json.dump(report, f)

    with open('report/result.json', 'w') as f:
        json.dump(report, f)


def colsByRowsToRowsByCols(values):
    ret = []
    for i in range(len(values[0])):
        row = [values[col][i] for col in range(len(values))]
        ret.append(row)
    return ret


def calculateStats(v):
    v.sort()
    stats = {}
    stats["min"] = v[0]
    stats["max"] = v[-1]
    stats["mean"] = sum(v)/len(v)
    stats["stddev"] = numpy.std(v)
    stats["q1"] = percentile(v, 0.25)
    stats["q2"] = percentile(v, 0.50)
    stats["q3"] = percentile(v, 0.75)
    stats["q9"] = percentile(v, 0.90)
    stats["q99"] = percentile(v, 0.99)
    return stats


def percentile(v, percent):
    k = (len(v)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return v[int(k)]
    d0 = v[int(f)] * (c-k)
    d1 = v[int(c)] * (k-f)
    return d0+d1


def readLog(path):
    headers = []
    values = []
    with open(path, 'r') as f:
        headersLine = f.next()
        headers = headersLine.strip().split(',')
        for i in range(len(headers)):
            values.append([])
        for line in f:
            if line == headersLine:
                continue
            if len(line.strip()) == 0:
                continue
            j = 0
            for x in line.split(','):
                try:
                    values[j].append(float(x))
                except ValueError as ex:
                    print "problem in column {0} in line '{1}' in file {2}\n".format(j, line, path);
                    raise ex
                j += 1
    return headers, values


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: report.py srcdir"
    else:
        main(sys.argv[1])
