#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

long long current_timestamp() {
    struct timeval te;
    gettimeofday(&te, NULL);
    return te.tv_sec*1000LL + te.tv_usec/1000;
}

int main(int argc, char** argv) {
  int time;
  int n;
  int i;
  for (i = 1; i < argc; i++) {
    char* val = strchr(argv[i], '=');
    if (val == NULL) {
      continue;
    }
    val++;
    if (strncmp("n", argv[i], 1) == 0) {
      n = atoi(val);
    } else if(strncmp("time", argv[i], 4) == 0) {
      time = atoi(val);
    }
  }
  unsigned int sleep = time * 1000;
  printf("actual sleep (ms)\n");
  long long then = current_timestamp();
  long long now;
  for (i = 0; i < n; i++) {
    usleep(sleep);
    now = current_timestamp();
    printf("%lld\n", now-then);
    then = now;
  }
}
