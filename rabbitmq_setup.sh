echo deb http://www.rabbitmq.com/debian/ testing main >> /etc/apt/sources.list
apt-get update
apt-get install --force-yes -y rabbitmq-server
rabbitmq-plugins enable rabbitmq_management
