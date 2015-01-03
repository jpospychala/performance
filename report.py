import json
import sys

def main(srcdir):
    report = []
    try:
      with open('{0}/index.json'.format(srcdir), 'r') as f:
        index = json.load(f)
    except:
      index = []

    for entry in index:
        logPath = 'results/{0}/{1}.log'.format(entry["id"], entry["params"]["task"])
        headers, values = readLog(logPath)
        stats = []
        for v in values:
            stats.append(calculateStats(v))
        entry.update({"headers": headers, "values": values, "stats": stats})
        report.append(entry)

  json.dump(report, sys.stdout)


def calculateStats(v):
    stats = {}
    #stats["min"] = 
    return stats


def readLog(path):
    headers = []
    values = []
    with open(path, 'r') as f:
        first = True
        for line in f:
            if first:
                headers = line.strip().split(',')
                first = False
            else:
                values.append([int(x) for x in line.split(',')])
    return headers, values


if __name__ == "__main__":
  main(sys.argv[2])
