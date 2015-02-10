#!/usr/bin/env python

import os
import sys
import getopt
import json
import subprocess
import re
import md5
import time
import socket

def main(argv):
  options = {
    "overwrite": False,
    "verbose": False,
    "dryRun": False,
    "doBuild": False,
    "quiet": False,
    "instance": None
  }
  configFileName = 'config.json'
  logPath = '~/.runner.log'

  try:
    opts, args = getopt.getopt(argv, "hbovqdc:i:", ["help", "build", "overwrite", "verbose", "quite", "dryrun", "config", "instance"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit()
    if opt in ("-b", "--build"):
      options["doBuild"] = True
    if opt in ("-o", "--overwrite"):
      options["overwrite"] = True
    if opt in ("-v", "--verbose"):
      options["verbose"] = True
    if opt in ("-q", "--quiet"):
      options["quiet"] = True
    if opt in ("-d", "--dryrun"):
      options["dryRun"] = True
    if opt in ("-c", "--config"):
      configFileName = arg
    if opt in ("-i", "--instance"):
      if len(arg) > 0 and arg[0] == '@':
        with open(os.path.expanduser(arg[1:]), 'r') as f:
          options["instances"] = [line.strip() for line in f]
      else:
        options["instances"] = [arg]

  options["configName"] = args and args.pop(0)
  with open(os.path.expanduser(configFileName), 'r') as f:
    configFile = json.load(f)

  try:
    with open('results/index.json', 'r') as f:
      report = json.load(f)
  except:
    report = []

  logFile = open(os.path.expanduser(logPath), 'a+')
  # TODO continue moving args into map
  process(configFile, report, logFile, options)
  logFile.close()

def usage():
  print "runner.py [-hadv] [-c config_file] [config]"
  print "-a --append     append results rather than overwrite"
  print "-b --build      run build step if configured"
  print "-c config_file  configuration file, default: config.json"
  print "-d --dryrun     don't actually run anything"
  print "-h              print this information"
  print "-v --verbose    verbose"
  print "-q --quiet    quiet"


def process(configFile, runreport, logFile, options):
  info = sysinfo()
  for name, config in configFile.items():
    if options["configName"] and name != options["configName"]:
      continue

    if not options["quiet"]:
      print name

    allVariants = []
    optionsKeys = config['options'].keys()
    config['options'].update({'config_name': name})
    config['options'].update(info)
    variantsList = variants(config['options'])
    for variant in variantsList:
      c = config.copy()
      c.update({"config": variant})
      allVariants.append(c)

    actuallyRanVariant = 0
    i = 0;
    n = len(allVariants)
    for variant in allVariants:
      i += 1
      id = createId(variant)
      cfgDetails = json.dumps(pick(optionsKeys, variant["config"]), sort_keys=True)

      isOneOfExpectedInstances = "instances" not in options or id in options["instances"] or cfgDetails in options["instances"]
      if not isOneOfExpectedInstances:
          continue

      wasRun = [r["id"] for r in runreport if r["id"] == id]

      if wasRun and not options["overwrite"]:
          if not options["quiet"]:
              print '{0}/{1} {2} skipping {3}'.format(i, n, id, cfgDetails)
          continue

      if options["quiet"]:
        print '{0}'.format(cfgDetails)
      else:
        print '{0}/{1} {2} executing {3}'.format(i, n, id, cfgDetails)
      sys.stdout.flush()

      if options["dryRun"]:
        continue

      if actuallyRanVariant == 0:
        if options["doBuild"] and "build" in config:
          ret = subprocess.call(config["build"], cwd=config.get("workdir"), stdout=logFile, stderr=logFile)
          if ret != 0:
            raise RuntimeError('build failed. Command: {0}'.format(config["build"]))

        if "before" in config:
          ret = subprocess.call(config["before"], cwd=config.get("workdir"), stdout=logFile, stderr=logFile)
          if ret != 0:
            raise RuntimeError('before step failed. Command: {0}'.format(config["before"]))

      actuallyRanVariant += 1
      logpaths = run(variant, id, options["verbose"])

      for task, path in logpaths.items():
        params = variant["config"].copy()
        params.update({"task": task})
        runreport.append({"id": id, "params": params})

        # update report file continuously
        with open('results/index.json', 'w') as f:
          json.dump(runreport, f)

    if actuallyRanVariant > 0 and not options["dryRun"] and "after" in config:
      ret = subprocess.call(config["after"], cwd=config.get("workdir"), stdout=logFile, stderr=logFile)
      if ret != 0:
        raise RuntimeError('after step failed. Command: {0}'.format(config["after"]))


def run(config, id, verbose):
  logdir = 'results/'+id+'/'
  processesToWait = []
  processesToKill = []
  logPaths = {}
  logFiles = []
  if not os.path.exists(logdir):
    os.makedirs(logdir)
  cwd = config.get("workdir")
  if "beforeEach" in config:
    ret = subprocess.call(config["beforeEach"] + [json.dumps(config["config"])], cwd=cwd)
    if ret != 0:
      raise RuntimeError('beforeEach step failed. Command: {0}'.format(config["beforeEach"]))
  if "wait_for_port" in config:
    wait_for_port(int(config["wait_for_port"]))
  for taskName, t in config["tasks"].items():
    logpath = logdir + taskName + '.log'
    logPaths[taskName] = logpath
    if verbose:
      print logpath
    logPathF=open(logpath,'w+')
    logFiles.append(logPathF)
    threadsCount = config["config"].get(taskName + "Threads", 1)
    if t.get("kill", False):
        processesList = processesToKill
    else:
        processesList = processesToWait
    for i in range(threadsCount):
      p = subprocess.Popen(t["cmd"] + params(config), stdout=logPathF, cwd=cwd)
      processesList.append(p)
  for p in processesToWait:
    ret = p.wait()
    if ret != 0:
        raise RuntimeError('process returned {0}'.format(ret))
  for p in processesToKill:
      p.kill()
  for logFile in logFiles:
    logFile.close()
  if "afterEach" in config:
    ret = subprocess.call(config["afterEach"] + [json.dumps(config["config"])], cwd=cwd)
    if ret != 0:
      raise RuntimeError('afterEach step failed. Command: {0}'.format(config["afterEach"]))
  return logPaths


def params(config):
  params = [json.dumps(config["config"])]
  if config.get("params_style") == "key_value":
    params = ["{0}={1}".format(k, v) for k, v in config["config"].items()]
  return params


def createId(variant):
  idmd5 = md5.new()
  idmd5.update(json.dumps(variant["config"], sort_keys=True))
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


def pick(keys, obj):
  return { key: obj[key] for key in keys }

def read_procfile(path):
  out = {}
  try:
    with open(path, 'r') as f:
      for l in f:
        key_val = [x.strip() for x in l.split(':')]
        if len(key_val) == 2:
          out[key_val[0]] = key_val[1]
  except:
    pass
  return out


def sysinfo():
  all = read_procfile('/proc/cpuinfo')
  cpuinfo = dict([(k, all.get(k, '')) for k in ['cpu cores', 'model name']])
  all = read_procfile('/proc/meminfo')
  meminfo = dict([(k, all.get(k, '')) for k in ['MemTotal']])
  oslabel = None
  path = os.path.expanduser('~/.perflabel')
  if os.path.isfile(path):
    with open(path, 'r') as f:
      oslabel = f.next().strip()
  out = {}
  out.update(cpuinfo)
  out.update(meminfo)
  if oslabel:
      out['oslabel'] = oslabel
  return out


def wait_for_port(port):
    port_is_open = False
    while not port_is_open:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost',port))
        port_is_open = result == 0
        time.sleep(3)
    return port_is_open

if __name__ == "__main__":
  main(sys.argv[1:])
