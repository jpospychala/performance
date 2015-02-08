#!/bin/sh

LOG=~/.run.log
set -e # fail fast
set -x # extra verbose
if [ ! -e ~/.perflabel ]; then
  locale-gen en_US
  dpkg-reconfigure locales
  apt-get update >> $LOG 2>&1
  apt-get -y install python-software-properties >> $LOG 2>&1
  add-apt-repository -y ppa:webupd8team/java >> $LOG 2>&1
  apt-get update >> $LOG 2>&1
  apt-get -y install git node.js gcc make docker.io npm g++ libzmq-dev >> $LOG 2>&1
  echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections >> $LOG 2>&1
  echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections >> $LOG 2>&1
  apt-get -y install oracle-java8-installer >> $LOG 2>&1
  apt-get -y install maven2 >> $LOG 2>&1
  ln -s /usr/bin/nodejs /usr/bin/node >> $LOG 2>&1
  echo LABEL > ~/.perflabel
fi

if [ -e performance ]; then
  cd performance
  git pull --rebase
else
  git clone https://github.com/jpospychala/performance.git
  cd performance
  npm install
fi

rm -rf results
rm -rf results.tar.gz

if [ -e ~/index.json -a ! -e results/index.json ]; then
  mkdir -p results
  cp ~/index.json results/index.json
fi

if [ -e ~/cfgstorun.txt ]; then
  ./runner.py -b -i @~/cfgstorun.txt
else
  ./runner.py -b #EXTRAARG
fi
tar czf results.tar.gz results
