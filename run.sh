#!/bin/sh

set -x
echo digitalocean512 > ~/.perflabel
apt-get update
apt-get -y install git node.js gcc make docker.io npm g++ python-software-properties libzmq-dev
add-apt-repository -y ppa:webupd8team/java
apt-get update
echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections
apt-get -y install oracle-java8-installer
apt-get -y install maven2
ln -s /usr/bin/nodejs /usr/bin/node
git clone https://github.com/jpospychala/performance.git
cd performance
npm install

./runner.py -b
