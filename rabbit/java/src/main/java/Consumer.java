import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.QueueingConsumer;

public class Consumer {

  public static void main(String[] argv) throws Exception {
    Map<String, String> params = new HashMap<String, String>();
    Arrays.asList(argv).stream()
    .forEach(s -> { String[] ss = s.split("="); params.put(ss[0], ss[1]); } );
    String queueName = params.get("queue");
    int msgsToSend = Integer.parseInt(params.get("msgsToSend"));
    int msgAckDelay = Integer.parseInt(params.get("msgAckDelay"));
    int prefetchCount = Integer.parseInt(params.get("prefetchCount"));
    boolean autoAck = Boolean.parseBoolean(params.get("autoAck"));

    System.out.println("ts (ms),time (ms),latency (ms),consume (ms)");

    ConnectionFactory factory = new ConnectionFactory();
    factory.setHost("localhost");
    Connection connection = factory.newConnection();
    Channel channel = connection.createChannel();
    channel.basicQos(prefetchCount);

    channel.queueDeclare(queueName, false, false, true, null);

    QueueingConsumer consumer = new QueueingConsumer(channel);
    channel.basicConsume(queueName, autoAck, consumer);

    long last = -1;
    long start = 0;
    for (int i = 0; i < msgsToSend; i++) {
      QueueingConsumer.Delivery delivery = consumer.nextDelivery();
      long now = System.currentTimeMillis();

      long then = Long.parseLong(new String(delivery.getBody()));
      if (last == -1) {
    	  start = now;
    	  last = now;
      }
      System.out.println(now+","+(now-start)+","+(now-then)+","+(now-last));
      last = now;

      if (msgAckDelay > 0) {
    	  Thread.sleep(msgAckDelay);
      }

      if (!autoAck) {
    	  channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
      }
    }
    channel.close();
    connection.close();
  }
}
