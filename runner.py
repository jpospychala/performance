#!/usr/bin/env python

import os
import sys
import getopt
import json
import subprocess
import re
import md5

def main(argv):
  overwrite = False
  verbose = False
  dryRun = False
  doBuild = False
  configFileName = 'config.json'
  instance = None

  try:
    opts, args = getopt.getopt(argv, "hbovdc:i:", ["help", "build", "overwrite", "verbose", "dryrun", "config", "instance"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    if opt in ("-b", "--build"):
      doBuild = True
    if opt in ("-o", "--overwrite"):
      overwrite = True
    if opt in ("-v", "--verbose"):
      verbose = True
    if opt in ("-d", "--dryrun"):
      dryRun = True
    if opt in ("-c", "--config"):
      configFileName = arg
    if opt in ("-i", "--instance"):
      instance = arg

  configName = args and args.pop(0)

  with open(configFileName, 'r') as f:
    configFile = json.load(f)

  with open('report/result.json', 'r') as f:
    report = json.load(f)

  process(configFile, configName, report, verbose, dryRun, doBuild, instance, overwrite)

def usage():
  print "runner.py [-hadv] [-c config_file] [config]"
  print "-a --append     append results rather than overwrite"
  print "-b --build      run build step if configured"
  print "-c config_file  configuration file, default: config.json"
  print "-d --dryrun     don't actually run anything"
  print "-h              print this information"
  print "-v --verbose    verbose"


def process(configFile, configName, runreport, verbose, dryRun, doBuild, instance, overwrite):
  allVariants = []
  for name, config in configFile.items():
    if not configName or name == configName:
      print name
      if not dryRun and doBuild and "build" in config:
          cwd = None
          if "workdir" in config:
              cwd = config["workdir"]
          subprocess.call(config["build"], cwd=cwd)
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

    if instance != None and instance != id:
        continue

    wasRun = [r["id"] for r in runreport if r["id"] == id]
    if not overwrite and wasRun and id != instance:
        print '{0}/{1} {2} skipping {3} {2}'.format(i, n, id, json.dumps(variant["config"]))
        continue

    print '{0}/{1} executing {3} {2}'.format(i, n, id, json.dumps(variant["config"]))

    if dryRun:
      continue

    logpaths = run(variant, id, verbose)
    for task, path in logpaths.items():
      headers, values = readLog(path)
      params = variant["config"].copy()
      params.update({"task": task})
      runreport.append({"id": id, "params": params, "headers": headers, "values": values})

      # update report file continuously
      with open('report/result.json', 'w') as f:
        json.dump(runreport, f)


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


def run(config, id, verbose):
  logdir = 'results/'+id+'/'
  processes = []
  logPaths = {}
  if not os.path.exists(logdir):
    os.makedirs(logdir)
  cwd = None
  if "workdir" in config:
    cwd = config["workdir"]
  if "before" in config:
    subprocess.call(config["before"], cwd=cwd)
  for taskName, t in config["tasks"].items():
    logpath = logdir + taskName + '.log'
    logPaths[taskName] = logpath
    if verbose:
      print logpath
    p = subprocess.Popen(t + [json.dumps(config["config"])], stdout=open(logpath,'w+'), cwd=cwd)
    processes.append(p)
  for p in processes:
    p.wait()
  if "after" in config:
    subprocess.call(config["after"], cwd=cwd)
  return logPaths


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

if __name__ == "__main__":
  main(sys.argv[1:])
