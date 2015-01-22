var amqp = require('amqplib');
var when = require('when');
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;
var padding = new Array(Math.max(0, config.msgSize - (Date.now()+'').length)).join(' ');

setTimeout(start, 1000);

console.log('time (ms)');
function start() {
    amqp.connect('amqp://localhost').then(function(conn) {
      return when(conn.createChannel().then(function(ch) {
        var q = config.queue;
        var ok = ch.checkQueue(q);

        return ok.then(function(_qok) {
          return when.promise(function(resolve, reject, notify) {
            var start = Date.now();

            setIntOrNow(sendMessage, config.msgSendDelay);

            function sendMessage() {
              if (msgsToSend <= 0) {
                ch.close().then(resolve);
                return;
              } else {
                var now = Date.now();
                var msg = padding + (now);
                msgsToSend--;
                ch.sendToQueue(q, new Buffer(msg), {deliveryMode: config.deliveryMode})
                console.log((now-start));
                setIntOrNow(sendMessage, config.msgSendDelay);
              }
            };
          });
        });
      })).ensure(function() { conn.close(); });;
    }).then(null, console.warn);
};

function setIntOrNow(fn, delay) {
  if (delay === 0) {
    setImmediate(fn);
  } else {
    return setTimeout(fn, delay);
  }
}
