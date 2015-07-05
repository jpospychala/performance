var fs = require('fs');

console.log('cpu user,cpu nice,cpu system,cpu idle,cpu iowait,mem used (MB),mem cached (MB)');

var now = Date.now();
var cpuLoad0 = cpuLoad();
setInterval(measure, 1000);

function measure() {
  console.log(cpuLoadDyn()+','+memUse());
}

function cpuLoad() {
  var loadStr = fs.readFileSync('/proc/stat').toString();
  var load = loadStr.split('\n')[0].split(' ').slice(2, 7).map(function(n) {return 1*n});
  return load;
}

function cpuLoadDyn() {
  var then = Date.now();
  var load = cpuLoad();
  var ret = [];
  for (var i = 0; i < load.length; i++) {
    ret[i] = Math.round((load[i] - cpuLoad0[i]) * 1000 / (then - now));
  }
  now = then;
  cpuLoad0 = load;
  return ret;
}

function memUse() {
  var memStr = fs.readFileSync('/proc/meminfo').toString();
  var mem = {}
  memStr.split('\n').map(function(l) {
    return l.split(':').map(function(f) {return f.trim()});
  })
  .filter(function(entry) { return ['MemTotal', 'MemFree', 'Cached'].indexOf(entry[0]) > -1; })
  .forEach(function(entry) {
    mem[entry[0]] = +entry[1].split(' ')[0];
  });
  return Math.round((mem.MemTotal-mem.MemFree)/1024)+','+Math.round(mem.Cached/1024);
}
