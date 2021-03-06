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
import traceback

runner = None

def main(argv):
  options = {
    "overwrite": False,
    "verbose": False,
    "dryRun": False,
    "doBuild": False,
    "quiet": False,
    "instance": None,
    "port": 9081,
    "resultsDir": 'results'
  }
  configFileName = 'config.json'

  try:
    opts, args = getopt.getopt(argv, "hbovqnc:i:d:r:", ["help", "build", "overwrite", "verbose", "quite", "dryrun", "config", "instance", "daemon", "results"])
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
    if opt in ("-n", "--dryrun"):
      options["dryRun"] = True
    if opt in ("-c", "--config"):
      configFileName = arg
    if opt in ("-d", "--daemon"):
      options["port"] = int(arg)
    if opt in ("-r", "--results"):
        options["resultsDir"] = arg
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
    with open('{0}/index.json'.format(options["resultsDir"]), 'r') as f:
      report = json.load(f)
  except:
    report = []

  global runner
  runner = Runner(configFile, report, options)
  if options["port"]:
    daemon(options["port"])
  else:
    runner.processAll()


def usage():
  print "runner.py [-hadv] [-c config_file] [-i instance] [-D port] [config]"
  print "-a --append     append results rather than overwrite"
  print "-b --build      run build step if configured"
  print "-c config_file  configuration file, default: config.json"
  print "-n --dryrun     don't actually run anything"
  print "-i instance     run specific instance or list of configs if instance starts with @"
  print "-d --daemon port  listen for commands on port"
  print "-h --help       print this information"
  print "-v --verbose    verbose"
  print "-q --quiet      quiet"


def daemon(port):
    bottle.run(host='0.0.0.0', port=port)


@bottle.get('/ping')
def daemon_ping():
    bottle.response.content_type = 'application/json'
    return json.dumps(sysinfo())


@bottle.post('/run')
def daemon_run():
    bottle.response.content_type = 'application/json'
    cfg = bottle.request.json
    result = runner.process(cfg)
    if "error" in result:
        return json.dumps(result)
    else:
        return json.dumps({"result": result})


@bottle.post('/name')
def daemon_name():
    bottle.response.content_type = 'application/json'
    cfg = bottle.request.json
    runner.info['oslabel'] = cfg['name']
    return json.dumps("my_name_is", runner.info['oslabel'])


@bottle.get('/log/<id>/<task>')
def daemon_logfile(id, task):
    return bottle.static_file("{0}.log".format(task), root='{0}/{1}/'.format(runner.options["resultsDir"], id))


@bottle.get('/results')
def daemon_run():
    bottle.response.content_type = 'application/json'
    result = runner.runreport
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

    def __init__(self, configFile, runreport, options):
        self.configFile = configFile
        self.runreport = runreport
        self.options = options
        self.built = []
        self.lastRanConfig = None
        self.info = sysinfo()


    def build(self, config, logFile):
        self.verbose("build")
        if config['@config'] in self.built:
            return
        self.built.append(config['@config'])
        if self.options["doBuild"] and "build" in config:
            self.verbose("build")
            ret = subprocess.call(config["build"], cwd=config.get("workdir"), stdout=logFile, stderr=logFile)
            if ret != 0:
                raise RuntimeError('build step failed. Command: {0}'.format(config["build"]))


    def beforeAll(self, config, logFile):
        self.verbose("beforeAll")
        if self.lastRanConfig is not None and config['@config'] == self.lastRanConfig['@config']:
            return
        self.lastRanConfig = config
        if not self.options["dryRun"] and "before" in config:
            self.verbose("beforeAll")
            ret = subprocess.call(config["before"], cwd=config.get("workdir"), stdout=logFile, stderr=logFile)
            if ret != 0:
                raise RuntimeError('before step failed. Command: {0}'.format(config["before"]))


    def afterAll(self, next=None, logFile=None):
        self.verbose("afterAll {0} {1}".format(self.lastRanConfig, next))
        if self.lastRanConfig is None:
            return
        if next is not None and next['@config'] == self.lastRanConfig['@config']:
            return
        if not self.options["dryRun"] and "after" in self.lastRanConfig:
            self.verbose("afterAll")
            ret = subprocess.call(self.lastRanConfig["after"], cwd=self.lastRanConfig.get("workdir"), stdout=logFile, stderr=logFile)
            if ret != 0:
                raise RuntimeError('after step failed. Command: {0}'.format(self.lastRanConfig["after"]))


    def beforeEach(self, config, logFile):
        self.verbose("beforeEach")
        if "beforeEach" in config:
            self.verbose("beforeEach")
            cwd = config.get("workdir")
            ret = subprocess.call(config["beforeEach"], cwd=cwd, stdout=logFile, stderr=logFile)
            if ret != 0:
                raise RuntimeError('beforeEach step failed. Command: {0}'.format(config["beforeEach"]))


    def afterEach(self, config, logFile):
        self.verbose("afterEach")
        if "afterEach" in config:
            self.verbose("afterEach")
            cwd = config.get("workdir")
            ret = subprocess.call(config["afterEach"], cwd=cwd, stdout=logFile, stderr=logFile)
            if ret != 0:
                raise RuntimeError('afterEach step failed. Command: {0}'.format(config["afterEach"]))


    def log(self, message):
        if self.options["quiet"]:
            return
        print message
        sys.stdout.flush()


    def verbose(self, message):
        if not self.options['verbose']:
            return
        print message
        sys.stdout.flush()

    def variants(self):
        allVariants = []
        for name, config in self.configFile.items():
            if self.options["configName"] and name != self.options["configName"]:
                continue

            config['options'].update({'@config': name})
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
        c['@config'] = cfgName
        c.update({"config": variant})
        del c['config']['@config']
        return c


    def processAll(self):
      allVariants = self.variants()
      n = len(allVariants)
      for v in allVariants:
          self.process(v)
      self.afterAll()


    def process(self, v):
        try:
            self.verbose("process {0}".format(v))
            variant = self.completeVariant(v)
            self.log('{0}'.format(json.dumps(v)))

            if self.options["dryRun"]:
                return []

            id = createId(variant)
            self.verbose("id {0}".format(id))
            wasRun = [r for r in self.runreport if r["id"] == id]
            self.verbose("wasRun {0}".format(wasRun))
            if wasRun and not self.options["overwrite"]:
                return wasRun

            logdir = self.options["resultsDir"]+'/'+id+'/'
            if not os.path.exists(logdir):
              os.makedirs(logdir)
            with open(logdir+'log.log', 'w+') as logFile:
                logFile.write('start!')
                self.afterAll(variant, logFile)
                self.build(variant, logFile)
                self.beforeAll(variant, logFile)
                self.beforeEach(variant, logFile)
                wait_for_port(variant.get("wait_for_port"))
                results = self.run(variant, logdir, logFile)
                self.runreport.extend(results)
                with open('{0}/index.json'.format(self.options["resultsDir"]), 'w') as f:
                    json.dump(self.runreport, f)
                self.afterEach(variant, logFile)
                self.verbose("processed {0}: {1}".format(v, results))
                logFile.write('processed!')
            return results;
        except RuntimeError as ex:
            return {"id": id, "error": ex.message}
        except EnvironmentError as ex:
            return {"id": id, "error": str(ex)}
        except:
            traceback.print_exc()
            return {"id": id, "error": str(sys.exc_info()[0])}


    def run(self, config, logdir, logFile):
      self.verbose("run {0}".format(config))
      id = createId(config)
      verbose = self.options["verbose"]
      cwd = config.get("workdir")
      processesToWait = []
      processesToKill = []
      logPaths = {}
      logFiles = []
      for taskName, t in config["tasks"].items():
        logpath = logdir + taskName + '.log'
        logPaths[taskName] = logpath
        if verbose:
          print logpath
        logPathF=open(logpath,'w+')
        logFiles.append(logPathF)
        threadsCount = config["config"].get(taskName + "s", 1)
        if t.get("kill", False):
            processesList = processesToKill
        else:
            processesList = processesToWait
        for i in range(threadsCount):
          cmdLine = t["cmd"] + params(config)
          self.verbose("run command: "+" ".join(cmdLine))
          p = subprocess.Popen(cmdLine, stdout=logPathF, stderr=logFile, cwd=cwd)
          processesList.append(p)

      try:
          self.verbose("waitfor {0} processes".format(len(processesToWait)))
          waitFor(processesToWait, config["config"].get("_timeout", 150))
      finally:
          self.verbose("killing {0} subprocesses".format(len(processesToWait + processesToKill)))
          for p in processesToWait + processesToKill:
              if p.poll() is None:
                p.kill()
          for logFile in logFiles:
              logFile.close()
          self.verbose('killed')

      result = []
      for task, path in logPaths.items():
          result.append({"id": id, "@config": config['@config'], "task": task, "params": config["config"], "sysinfo": self.info})
      return result

    def tailLog(self, lines=100):
        lines = []
        with open(os.path.expanduser(logPath), 'r') as f:
            for l in f:
                lines.insert(0, l)
                if len(lines) > 99:
                    lines[:] = lines[0:99]
        return lines

def waitFor(processesToWait, timeout):
    deadline = time.time() + timeout
    while len(processesToWait) > 0:
        if time.time() > deadline:
            raise RuntimeError('timed out ({0} sec)'.format(timeout))
        toRemove = []
        time.sleep(0.5)
        for p in processesToWait:
          ret = p.poll()
          if ret != None:
              toRemove.append(p)
              if ret != 0:
                  raise RuntimeError('process returned {0}'.format(ret))
        for p in toRemove:
            processesToWait.remove(p)


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
  out = {}
  out.update(cpuinfo)
  out.update(meminfo)
  out['oslabel'] = ''
  return out


def wait_for_port(port, timeout=30):
    if port is None:
        return
    port = int(port)
    port_is_open = False
    deadline = time.time() + timeout
    while not port_is_open:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost',port))
        port_is_open = result == 0
        time.sleep(3)
        if time.time() > deadline:
            raise RuntimeError('timed out waiting for port {0}'.format(port))
    return port_is_open


if __name__ == "__main__":
  main(sys.argv[1:])
