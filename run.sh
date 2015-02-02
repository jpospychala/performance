#!/bin/sh

set -e # fail fast
set -x # extra verbose
if [ ! -e ~/.perflabel ]; then
  apt-get update
  apt-get -y install python-software-properties
  add-apt-repository -y ppa:webupd8team/java
  apt-get update
  apt-get -y install git node.js gcc make docker.io npm g++ libzmq-dev
  echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections
  echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections
  apt-get -y install oracle-java8-installer
  apt-get -y install maven2
  ln -s /usr/bin/nodejs /usr/bin/node
  echo digitalocean512 > ~/.perflabel
fi

if [ -e performance ]; then
  cd performance
  git pull --rebase
else
  git clone https://github.com/jpospychala/performance.git
  cd performance
  npm install
fi

if [ -e ~/index.json -a ! -e results/index.json ]; then
  mkdir results
  cp ~/index.json results/index.json
fi

if [ -e ~/cfgstorun.txt ]; then
  cat ~/cfgstorun.txt | while read L; do ./runner.py -b -i "$L"; done
else
  ./runner.py -b #EXTRAARG
fi
tar czvf results.tar.gz results
