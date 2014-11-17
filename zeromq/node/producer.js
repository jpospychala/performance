var zmq = require('zmq')
var publisher = zmq.socket('pub')
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;
var padding = new Array(Math.max(0, config.msgSize - (Date.now()+'').length)).join(' ');

publisher.bind('tcp://*:8688', function(err) {
  if(err)
    console.log(err);
  else
    setTimeout(start, 1000);
});

function start() {
  console.log('ts (ms),time (ms)');
  var start = Date.now();
  var intervalObj = setInterval(function() {
      if (msgsToSend <= 0) {
        clearInterval(intervalObj);
        publisher.close();
        return;
      }

      var now = Date.now();
      var msg = padding + now;
      msgsToSend--;
      publisher.send(msg)
      console.log(now+','+(now-start));
  }, config.msgSendDelay);
}
