var amqp = require('amqplib');
var config = JSON.parse(process.argv[2]);

amqp.connect('amqp://localhost').then(function(conn) {
  process.once('SIGINT', function() { conn.close(); });
  return conn.createChannel()
  .then(function(ch) {
    return ch.deleteQueue(config.queue);
  })
  .then(function() {
    return conn.close();
  });
});
