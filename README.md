Benchmark runner
================

This tool automates launching benchmark programs, collection and analysis of their results.

Benchmark is a program with a set of configuration parameters. Runner takes an array of
configuration params with possible values and runs the program for all combinations of
params. Each program run prints CSV-like output with measurements. Those are collected
and presented in web report tool.

Setup:
```
apt-get install git node.js gcc make docker.io npm g++ python-software-properties libzmq-dev
add-apt-repository ppa:webupd8team/java
apt-get update
apt-get install oracle-java8-installer
apt-get install maven2
npm install
```
Run the benchmark runner:
```
./runner.py [benchmark_name]
```

|Available benchmarks|Description                            |
|--------------------|---------------------------------------|
|sleep_node          |node setTimeout accuracy               |
|sleep_java          |Thread.sleep accuracy                  |
|sleep_c             |usleep(milisec) accuracy               |
|rabbitmq_nodejs     |producer-consumer latency, node amqplib|
|rabbitmq_java       |producer-consumer latency, Java Client |
|zeromq_nodejs       |producer-consumer latency, node zmq     |

See reports (requires npm install http-server):
```
http-server ./
visit http://localhost:8080/report
```

Launching benchmars on DigitalOcean:
------------------------------------

To make the tests repeatable, there's script that automates their invocation on
 DigitalOcean droplets. It requires an account on DO and DO API key available
 in environment variable $DOTOKEN. Example usage:

 ```bash
$ env | grep DOTOKEN
DOTOKEN=4db445b9gf4034jsdldalsdk23232b269k123123uf9hq8293ds
$ ./runner.py digitalocean:3:512m
# creates 3 DigitalOcean droplets with size 512m
# executes all benchmarks
$ ./report.py results/
# generates statistical data for newly obtained results
#
# now refresh report website to see new report
```
