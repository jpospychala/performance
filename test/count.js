var config = JSON.parse(process.argv[2]);

var i = 0;
function tick() {
  console.log(i++);
  if (i < config.max) {
    setTimeout(tick, config.delay);
  }
}

tick();
