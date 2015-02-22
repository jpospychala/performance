#!/usr/bin/env python

import os
import sys
import getopt
import json
import subprocess
import signal
import socket
import re
import md5
import time
import bottle

runner = None

def main(argv):
  options = {
    "overwrite": False,
    "verbose": False,
    "dryRun": False,
    "doBuild": False,
    "quiet": False,
    "instance": None,
    "port": None
  }
  configFileName = 'config.json'
  logPath = '~/.runner.log'

  try:
    opts, args = getopt.getopt(argv, "hbovqdc:i:p:", ["help", "build", "overwrite", "verbose", "quite", "dryrun", "config", "instance", "port"])
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
    if opt in ("-p", "--port"):
      options["port"] = int(arg)
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
  global runner
  runner = Runner(configFile, report, logFile, options)
  if options["port"]:
    daemon(options["port"])
  else:
    runner.processAll()
  logFile.close()


def usage():
  print "runner.py [-hadv] [-c config_file] [-i instance] [-D port] [config]"
  print "-a --append     append results rather than overwrite"
  print "-b --build      run build step if configured"
  print "-c config_file  configuration file, default: config.json"
  print "-d --dryrun     don't actually run anything"
  print "-i instance     run specific instance or list of configs if instance starts with @"
  print "-p --port port  listen for commands on port"
  print "-h              print this information"
  print "-v --verbose    verbose"
  print "-q --quiet      quiet"


def daemon(port):
    bottle.run(host='localhost', port=port)


@bottle.get('/ping')
def daemon_ping():
    bottle.response.content_type = 'application/json'
    return json.dumps(sysinfo())


@bottle.post('/run')
def daemon_run():
    bottle.response.content_type = 'application/json'
    cfg = bottle.request.json
    result = runner.process(cfg)
    return json.dumps({"result": result})


@bottle.get('/variants')
def daemon_run():
    bottle.response.content_type = 'application/json'
    variants = runner.variants()
    return json.dumps(variants)


@bottle.route('/close')
def daemon_close():
    print "shutting down"
    runner.afterAll()
    os.kill(os.getpid(), signal.SIGTERM)


class Runner:

    def __init__(self, configFile, runreport, logFile, options):
        self.configFile = configFile
        self.runreport = runreport
        self.logFile = logFile
        self.options = options
        self.built = []
        self.lastRanConfig = None
        self.info = sysinfo()


    def build(self, config):
        if config['config']['@config'] in self.built:
            return
        self.built.append(config['config']['@config'])
        if self.options["doBuild"] and "build" in config:
            ret = subprocess.call(config["build"], cwd=config.get("workdir"), stdout=self.logFile, stderr=self.logFile)
            if ret != 0:
                raise RuntimeError('build failed. Command: {0}'.format(config["build"]))


    def beforeAll(self, config):
        if self.lastRanConfig is not None and config['config']['@config'] == self.lastRanConfig['config']['@config']:
            return
        self.lastRanConfig = config
        if not self.options["dryRun"] and "before" in config:
            ret = subprocess.call(config["before"], cwd=config.get("workdir"), stdout=self.logFile, stderr=self.logFile)
            if ret != 0:
                raise RuntimeError('before step failed. Command: {0}'.format(config["before"]))


    def afterAll(self, next=None):
        if self.lastRanConfig is None:
            return
        if next is not None and next['config']['@config'] == self.lastRanConfig['config']['@config']:
            return
        if not self.options["dryRun"] and "after" in self.lastRanConfig:
            ret = subprocess.call(self.lastRanConfig["after"], cwd=self.lastRanConfig.get("workdir"), stdout=self.logFile, stderr=self.logFile)
            if ret != 0:
                raise RuntimeError('after step failed. Command: {0}'.format(self.lastRanConfig["after"]))


    def beforeEach(self, config):
        if "beforeEach" in config:
            cwd = config.get("workdir")
            ret = subprocess.call(config["beforeEach"] + [json.dumps(config["config"])], cwd=cwd)
            if ret != 0:
                raise RuntimeError('beforeEach step failed. Command: {0}'.format(config["beforeEach"]))


    def afterEach(self, config):
        if "afterEach" in config:
            cwd = config.get("workdir")
            ret = subprocess.call(config["afterEach"] + [json.dumps(config["config"])], cwd=cwd)
            if ret != 0:
                raise RuntimeError('afterEach step failed. Command: {0}'.format(config["afterEach"]))


    def log(self, message):
        if self.options["quiet"]:
            return
        print message
        sys.stdout.flush()


    def variants(self):
        allVariants = []
        for name, config in self.configFile.items():
            if self.options["configName"] and name != self.options["configName"]:
                continue

            config['options'].update({'@config': name, 'oslabel': self.info['oslabel']})
            variantsList = variants(config['options'])

            if "instances" in self.options:
                for variant in variantsList:
                    if variant in self.options["instances"]:
                        allVariants.append(variant)
            else:
                allVariants.extend(variantsList)
        return allVariants


    def completeVariant(self, variant):
        cfgName = variant['@config']
        config = self.configFile[cfgName]
        c = config.copy()
        c.update({"config": variant})
        c['config'].update(self.info)
        return c


    def processAll(self):
      allVariants = self.variants()
      n = len(allVariants)
      for v in allVariants:
          self.process(v)
      self.afterAll()


    def process(self, v):
        variant = self.completeVariant(v)
        self.log('{0}'.format(json.dumps(v)))

        if self.options["dryRun"]:
            return []

        id = createId(variant)
        wasRun = [r for r in self.runreport if r["id"] == id]
        if wasRun and not self.options["overwrite"]:
            return wasRun

        self.afterAll(variant)
        self.build(variant)
        self.beforeAll(variant)
        self.beforeEach(variant)
        wait_for_port(variant.get("wait_for_port"))
        results = self.run(variant)
        self.runreport.extend(results)
        with open('results/index.json', 'w') as f:
            json.dump(self.runreport, f)
        self.afterEach(variant)

        return results;


    def run(self, config):
      id = createId(config)
      verbose = self.options["verbose"]
      cwd = config.get("workdir")
      logdir = 'results/'+id+'/'
      processesToWait = []
      processesToKill = []
      logPaths = {}
      logFiles = []
      if not os.path.exists(logdir):
        os.makedirs(logdir)
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
      result = []
      for task, path in logPaths.items():
          p = config["config"].copy()
          p.update({"task": task})
          result.append({"id": id, "params": p})
      return result


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


def pickOptionsKeys(obj):
    blackList = ["@config", "cpu cores", "MemTotal", "model name", "oslabel"]
    return { key: obj[key] for key in obj.keys() if key not in blackList }


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
    if port is None:
        return
    port = int(port)
    port_is_open = False
    while not port_is_open:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost',port))
        port_is_open = result == 0
        time.sleep(3)
    return port_is_open


if __name__ == "__main__":
  main(sys.argv[1:])
