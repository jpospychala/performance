#!/bin/sh

LOG=~/.run.log
set -e # fail fast
if [ ! -e ~/.perflabel ]; then
  echo provisioning
  locale-gen en_US >> $LOG 2>&1
  apt-get update >> $LOG 2>&1
  apt-get -y install python-software-properties >> $LOG 2>&1
  add-apt-repository -y ppa:webupd8team/java >> $LOG 2>&1
  apt-get update >> $LOG 2>&1
  apt-get -y install python-pip git node.js gcc make docker.io npm g++ libzmq-dev >> $LOG 2>&1
  echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections >> $LOG 2>&1
  echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections >> $LOG 2>&1
  apt-get -y install oracle-java8-installer >> $LOG 2>&1
  apt-get -y install maven2 >> $LOG 2>&1
  pip install bottle >> $LOG 2>&1
  ln -s /usr/bin/nodejs /usr/bin/node >> $LOG 2>&1
  echo LABEL > ~/.perflabel
fi

if [ -e performance ]; then
  cd performance
  git pull --rebase
else
  git clone https://github.com/jpospychala/performance.git
  cd performance
  npm install >> $LOG 2>&1
fi

# kill previous runnerd instances
ps aux | grep 'python ./runnerd.py' | sed 's/  */ /g' | cut -f 2 -d ' ' | xargs kill

# TODO restart infinitely runnerd?
screen -d -m /bin/bash -c "./runnerd.py -vb >> $LOG 2>&1"
