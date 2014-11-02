var config = JSON.parse(process.argv[2]);

var start = new Date().getTime();
var last;
console.log('time (ms),ticks (n),actual sleep (ms)')
var i = 0;
function tick() {
  var now = new Date().getTime();
  if (last) {
    console.log([now-start, i++, now-last].join());
  }
  last = now;
  if (i < config.n) {
    setTimeout(tick, config.time);
  }
}

tick();
