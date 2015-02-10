import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import com.rabbitmq.client.AMQP.BasicProperties;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.Channel;

public class Producer {

  public static void main(String[] argv) throws Exception {
    Map<String, String> params = new HashMap<String, String>();
    Arrays.asList(argv).stream()
    .forEach(s -> { String[] ss = s.split("="); params.put(ss[0], ss[1]); } );
    String queueName = params.get("queue");
    int producerThreads = Integer.parseInt(params.get("producerThreads"));
    int msgsToSend = Integer.parseInt(params.get("msgsToSend")) / producerThreads;
    int msgSendDelay = Integer.parseInt(params.get("msgSendDelay"));
    int deliveryMode = Integer.parseInt(params.get("deliveryMode"));
    int msgSize = Integer.parseInt(params.get("msgSize"));
    BasicProperties msgProperties = new BasicProperties().builder()
    .deliveryMode(deliveryMode)
    .build();
    StringBuilder padding = new StringBuilder();
    for (int i = 0; i < Math.max(0, msgSize - Long.toString(System.currentTimeMillis()).length()); i++) {
      padding.append(' ');
    }

    ConnectionFactory factory = new ConnectionFactory();
    factory.setHost("localhost");
    Connection connection = factory.newConnection();
    Channel channel = connection.createChannel();

    Thread.sleep(1000);
    channel.queueDeclarePassive(queueName);

    System.out.print("time (ms)\n");
    long start = System.currentTimeMillis();
    for (int i = 0; i < msgsToSend; i++) {
        long now = System.currentTimeMillis();
        channel.basicPublish("", queueName, msgProperties, Long.toString(now).getBytes());
        System.out.print((now-start)+"\n");
        Thread.sleep(msgSendDelay);
    }

    channel.close();
    connection.close();
  }
}
