var amqp = require('amqplib');
var when = require('when');
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;

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

            var intervalObj = setInterval(function() {
                if (msgsToSend <= 0) {
                  clearInterval(intervalObj);
                  ch.close().then(resolve);
                  return;
                }

                var now = Date.now();
                var msg = '' + (now);
                msgsToSend--;
                ch.sendToQueue(q, new Buffer(msg), config.msgOpts)
                console.log(now-start);
            }, config.msgSendDelay);
          });
        });
      })).ensure(function() { conn.close(); });;
    }).then(null, console.warn);
};
