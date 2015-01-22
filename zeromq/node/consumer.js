var zmq = require('zmq')
var subscriber = zmq.socket('sub')
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;
var start;
var last;

console.log('time (ms),latency (ms),consume (ms)');
subscriber.on("message", function(msg) {
  var now = Date.now();
  var then = 1*msg.toString();
  if (last === undefined) {
    start = now;
    last = now;
  }
  console.log((now-start)+','+(now-then)+','+(now-last));
  last = now;

  msgsToSend--;
  if (msgsToSend == 0) {
    setImmediate(function() {subscriber.close();});
  }
})

subscriber.connect("tcp://localhost:8688")
subscriber.subscribe("")
