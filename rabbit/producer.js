var amqp = require('amqplib');
var when = require('when');
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;

amqp.connect('amqp://localhost').then(function(conn) {
  return when(conn.createChannel().then(function(ch) {
    var q = config.queue;

    var ok = ch.assertQueue(q, config.queueOpts);

    return ok.then(function(_qok) {
      return when.promise(function(resolve, reject, notify) {
        var intervalObj = setInterval(function() {
            if (msgsToSend <= 0) {
              clearInterval(intervalObj);
              ch.close().then(resolve);
              return;
            }

            var msg = '' + (new Date().getTime());
            msgsToSend--;
            ch.sendToQueue(q, new Buffer(msg), config.msgOpts)
        }, config.delayBetweenMsgs);
      });
    });
  })).ensure(function() { conn.close(); });;
}).then(null, console.warn);
