#!/usr/bin/env python

import os
import sys
import getopt
import json
import subprocess
import re
import md5
import time

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

  try:
    with open('report/result.json', 'r') as f:
      report = json.load(f)
  except:
    report = []

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
  for name, config in configFile.items():
    if configName and name != configName:
      continue

    print name
    allVariants = []
    config['options'].update({'config_name': name})
    variantsList = variants(config['options'])
    for variant in variantsList:
      c = config.copy()
      c.update({"config": variant})
      allVariants.append(c)

    if not dryRun and doBuild and "build" in config:
      subprocess.call(config["build"], cwd=config.get("workdir"))

    if not dryRun and "before" in config:
      subprocess.call(config["before"], cwd=config.get("workdir"))

    i = 0;
    n = len(allVariants)
    for variant in allVariants:
      i += 1
      id = createId(variant)

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

    if not dryRun and "before" in config:
      subprocess.call(config["before"], cwd=config.get("workdir"))


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
  cwd = config.get("workdir")
  if "beforeEach" in config:
    subprocess.call(config["beforeEach"], cwd=cwd)
  for taskName, t in config["tasks"].items():
    logpath = logdir + taskName + '.log'
    logPaths[taskName] = logpath
    if verbose:
      print logpath
    p = subprocess.Popen(t + params(config), stdout=open(logpath,'w+'), cwd=cwd)
    processes.append(p)
  for p in processes:
    p.wait()
  if "afterEach" in config:
    subprocess.call(config["afterEach"], cwd=cwd)
  return logPaths


def params(config):
  params = [json.dumps(config["config"])]
  if config.get("params_style") == "key_value":
    params = ["{0}={1}".format(k, v) for k, v in config["config"].items()]
  return params


def createId(variant):
  idmd5 = md5.new()
  idmd5.update(json.dumps(variant["config"]))
  return idmd5.hexdigest()


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
