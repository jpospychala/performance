import os
import sys
import getopt
import json
import subprocess
import re
import md5

def main(argv):
  appendToReport = False
  verbose = False

  try:
    opts, args = getopt.getopt(argv, "hav", ["help", "append", "verbose"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    if opt in ("-a", "--append"):
      appendToReport = True
    if opt in ("-v", "--verbose"):
      verbose = True

  if not args:
    usage()
    sys.exit(2)

  configFileName = args.pop(0)
  configName = args and args.pop(0)

  with open(configFileName, 'r') as f:
    configFile = json.load(f)

  report = []
  if appendToReport:
    with open('report/result.json', 'r') as f:
      report = json.load(f)

  process(configFile, configName, report, verbose)


def process(configFile, configName, runreport, verbose):
  allVariants = []
  for name, config in configFile.items():
    if not configName or name == configName:
      print name
      config['options'].update({'config_name': name})
      variantsList = variants(config['options'])
      for variant in variantsList:
        c = config.copy()
        c.update({"config": variant})
        allVariants.append(c)

  i = 0;
  n = len(allVariants)
  for variant in allVariants:
    i += 1
    idmd5 = md5.new()
    idmd5.update(json.dumps(variant["config"]))
    id = idmd5.hexdigest()
    if [r["id"] for r in runreport if r["id"] == id]:
        print '{0}/{1} skipping {2}'.format(i, n, json.dumps(variant["config"]))
        continue

    print '{0}/{1} executing {2}'.format(i, n, json.dumps(variant["config"]))

    logpaths = run(variant, id, verbose)
    for task, path in logpaths.items():
      log = readLog(path)
      params = variant["config"].copy()
      params.update({"task": task})
      runreport.append({"id": id, "params": params, "log": log})

    with open('report/result.json', 'w') as f:
      json.dump(runreport, f)


def readLog(path):
  values = []
  with open(path, 'r') as f:
    for line in f:
      values.append(int(line))
  return values


def run(config, id, verbose):
  logdir = 'results/'+id+'/'
  processes = []
  logs = {}
  if not os.path.exists(logdir):
    os.makedirs(logdir)
  print config
  if config["before"]:
    subprocess.call(config["before"])
  for taskName, t in config["tasks"].items():
    logpath = logdir + taskName + '.log'
    logs[taskName] = logpath
    if verbose:
      print logpath
    p = subprocess.Popen(t + [json.dumps(config["config"])], stdout=open(logpath,'w+'))
    processes.append(p)
  for p in processes:
    p.wait()
  if config["after"]:
    subprocess.call(config["after"])
  return logs


def variants(dict):
  if not dict:
    return [{}]

  results = []
  field, values = dict.popitem()

  if isinstance(values, basestring):
    values = [values]
  for v in values:
    subvariants = variants(dict)
    for subv in subvariants:
      subv[field] = v
      results.append(subv)
  dict[field] = values
  return results


def usage():
  print "runner.py [-ha] config_file [config]"
  print "-h           print this information"
  print "-a --append  append results rather than overwrite"


if __name__ == "__main__":
  main(sys.argv[1:])
