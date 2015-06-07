var config = JSON.parse(process.argv[2]);

var last;
console.log('actual sleep (ms)')
var i = 0;
function tick() {
  var now = Date.now();
  if (last) {
    console.log(now-last);
  }
  last = now;
  if (i++ < config.n) {
    setTimeout(tick, config.time);
  }
}

tick();
