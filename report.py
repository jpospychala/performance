#!/usr/bin/env python

import json
import sys
import math
import functools

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

    i = 0
    for entry in index:
        i += 1
        sys.stderr.write('\b\b\b\b{:0>3d}%'.format(i*100/len(index)))

        if reportHas(report, entry):
            continue

        logPath = 'results/{0}/{1}.log'.format(entry["id"], entry["params"]["task"])
        headers, values = readLog(logPath)
        stats = []
        for v in values:
            stats.append(calculateStats(v))
        entry.update({"headers": headers, "stats": stats})
        report.append(entry)

        if (i % 100) == 0 or i == len(index):
            with open('report/result.json', 'w') as f:
                json.dump(report, f)


def reportHas(report, e):
    for entry in report:
        if entry["id"] == e["id"] and entry["params"]["task"] == e["params"]["task"]:
            return True
    return False

def calculateStats(v):
    v.sort()
    stats = {}
    stats["min"] = v[0]
    stats["max"] = v[-1]
    stats["mean"] = sum(v)/len(v)
    stats["q1"] = percentile(v, 0.25)
    stats["q2"] = percentile(v, 0.50)
    stats["q3"] = percentile(v, 0.75)
    stats["q9"] = percentile(v, 0.90)
    stats["q99"] = percentile(v, 0.99)
    d = (v[-1] - v[0])
    if d > 0:
        stats["throughput"] = len(v)/d
    else:
        stats["throughput"] = 0
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
        headers = f.next().strip().split(',')
        for i in range(len(headers)):
            values.append([])
        for line in f:
            j = 0
            for x in line.split(','):
                values[j].append(int(x))
                j += 1
    return headers, values


if __name__ == "__main__":
    main(sys.argv[1])
