var amqp = require('amqplib');
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;

amqp.connect('amqp://localhost').then(function(conn) {
  process.once('SIGINT', function() { conn.close(); });
  return conn.createChannel().then(function(ch) {
    console.log('time (ms),latency (ms), consume (ms)');
    var ok = ch.assertQueue(config.queue, config.queueOpts)
    .then(function() {
      return ch.purgeQueue(config.queue);
    })
    .then(function() {
      return ch.prefetch(config.prefetchCount);
    })
    .then(function() {
      var start = Date.now();
      var last;

      return ch.consume(config.queue, function(msg) {
        var now = Date.now();
        var then = 1*msg.content.toString();
        if (last === undefined) {
          last = now;
        }
        console.log((now-start)+','+(now-then)+','+(now-last));
        last = now;

        if (config.msgAckDelay > 0) {
          setTimeout(ack, config.msgAckDelay);
        } else {
          ack();
        }

        function ack() {
          if (! config.consumerOpts.noAck) {
            ch.ack(msg);
          }
          msgsToSend--;
          if (msgsToSend == 0) {
            setImmediate(function() {conn.close();});
          }
        }
      }, config.consumerOpts);
    });
  });
}).then(null, console.warn);
