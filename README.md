Benchmark runner
================

This tool automates launching benchmark programs, collection and analysis of their results.

Benchmark is a program with a set of configuration parameters. Runner takes an array of
configuration params with possible values and runs the program for all combinations of
params. Each program run prints CSV-like output with measurements. Those are collected
and presented in web report tool.

Setup:
```
apt-get install git node.js gcc make docker.io npm maven2 python-software-properties
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer
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
|rabbits_latency     |producer-consumer latency, node amqplib|
|rabbits_latency_java|producer-consumer latency, Java Client |

See reports (requires npm install http-server):
```
cd report
http-server ./
visit http://localhost:8080
```
