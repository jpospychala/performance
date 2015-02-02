var fs = require('fs');

console.log('load (1min),mem use (kB)');

setInterval(measure, 1000);

function measure() {
  var loadStr = fs.readFileSync('/proc/loadavg').toString();
  var memStr = fs.readFileSync('/proc/meminfo').toString();

  var load = loadStr.trim().split(' ');
  var mem = {}
  memStr.split('\n').map(function(l) {
    return l.split(':').map(function(f) {return f.trim()});
  })
  .filter(function(entry) { return ['MemTotal', 'MemFree', 'Cached'].indexOf(entry[0]) > -1; })
  .forEach(function(entry) {
    mem[entry[0]] = +entry[1].split(' ')[0];
  });
  console.log(load[0]+','+(mem.MemTotal-mem.MemFree-mem.Cached));
}
