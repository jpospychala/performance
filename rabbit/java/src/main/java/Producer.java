import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rabbitmq.client.AMQP.BasicProperties;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.Channel;

public class Producer {

  public static void main(String[] argv) throws Exception {
	ObjectMapper m = new ObjectMapper();
	JsonNode config = m.readTree(argv[0]);
	String queueName = config.path("queue").textValue();
	int msgsToSend = config.path("msgsToSend").intValue();
	int msgSendDelay = config.path("msgSendDelay").intValue();
	int deliveryMode = config.path("deliveryMode").intValue();
	BasicProperties msgProperties = new BasicProperties().builder()
		.deliveryMode(deliveryMode)
		.build();

    ConnectionFactory factory = new ConnectionFactory();
    factory.setHost("localhost");
    Connection connection = factory.newConnection();
    Channel channel = connection.createChannel();
    
    Thread.sleep(1000);
    channel.queueDeclarePassive(queueName);
    
    System.out.println("ts (ms),time (ms)");
    long start = System.currentTimeMillis();
    for (int i = 0; i < msgsToSend; i++) {
        long now = System.currentTimeMillis();
        channel.basicPublish("", queueName, msgProperties, Long.toString(now).getBytes());
        System.out.println(now+","+(now-start));
        Thread.sleep(msgSendDelay);
    }
    
    channel.close();
    connection.close();
  }
}