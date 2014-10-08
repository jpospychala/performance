var amqp = require('amqplib');
var config = JSON.parse(process.argv[2]);

var msgsToSend = config.msgsToSend;

amqp.connect('amqp://localhost').then(function(conn) {
  process.once('SIGINT', function() { conn.close(); });
  return conn.createChannel().then(function(ch) {

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
        console.log(now-then);
        msgsToSend--;
        if (! config.consumerOpts.noAck) {
          ch.ack(msg);
        }
        if (msgsToSend == 0) {
          setImmediate(function() {conn.close();});
        }
      }, config.consumerOpts);
    });
  });
}).then(null, console.warn);
