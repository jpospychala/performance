var amqp = require('amqplib');
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;
var start = new Date().getTime();

amqp.connect('amqp://localhost').then(function(conn) {
  process.once('SIGINT', function() { conn.close(); });
  return conn.createChannel().then(function(ch) {

    console.log('time (ms),latency (ms)');
    var ok = ch.assertQueue(config.queue, config.queueOpts)
    .then(function() {
      return ch.purgeQueue(config.queue);
    })
    .then(function() {
      return ch.prefetch(config.prefetchCount);
    })
    .then(function() {
      return ch.consume(config.queue, function(msg) {
        var now = new Date().getTime();
        var then = 1*msg.content.toString();
        console.log((now-start)+','+(now-then));

        setTimeout(function() {
          if (! config.consumerOpts.noAck) {
            ch.ack(msg);
          }
          msgsToSend--;
          if (msgsToSend == 0) {
            setImmediate(function() {conn.close();});
          }
        }, config.msgAckDelay);
      }, config.consumerOpts);
    });
  });
}).then(null, console.warn);
