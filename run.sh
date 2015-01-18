#!/bin/sh

set -x
echo digitalocean512 > ~/.perflabel
apt-get -y install python-software-properties
add-apt-repository -y ppa:webupd8team/java
apt-get update
apt-get -y install git node.js gcc make docker.io npm g++ libzmq-dev
echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections
apt-get -y install oracle-java8-installer
apt-get -y install maven2
ln -s /usr/bin/nodejs /usr/bin/node

if [ -e performance ]; then
  cd performance
  git pull --rebase
else
  git clone https://github.com/jpospychala/performance.git
  cd performance
fi

npm install

if [ -e ~/index.json -a ! -e results/index.json ]; then
  mkdir results
  cp ~/index.json results/index.json
fi

./runner.py -b
tar czvf results.tar.gz results
