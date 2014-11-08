Benchmark runner
================

This tool automates launching benchmark programs, collection and analysis of their results.

Benchmark is a program with a set of configuration parameters. Runner takes an array of
configuration params with possible values and runs the program for all combinations of
params. Each program run prints CSV-like output with measurements. Those are collected
and presented in web report tool.

Run the benchmark runner:
```
./runner.py [benchmark_name]
```
See reports (requires npm install http-server):
```
cd report
http-server ./
visit http://localhost:8080
```
