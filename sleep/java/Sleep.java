import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

class Sleep {
  public static void main(String[] args) throws InterruptedException {
    Map<String, String> params = new HashMap<String, String>();
    Arrays.asList(args).stream()
    .forEach(s -> { String[] ss = s.split("="); params.put(ss[0], ss[1]); } );
    int n = Integer.parseInt(params.get("n"));
    int time = Integer.parseInt(params.get("time"));

    long last = System.currentTimeMillis();
    System.out.println("actual sleep (ms)");
    for (int i = 0; i < n; i++) {
      Thread.sleep(time);
      long now = System.currentTimeMillis();
      System.out.println(now-last);
      last = now;
    }
  }
}
