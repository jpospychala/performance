FROM ubuntu:14.04
MAINTAINER jacek.pospychala@gmail.com

RUN echo deb http://www.rabbitmq.com/debian/ testing main >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install --force-yes -y rabbitmq-server
RUN rabbitmq-plugins enable rabbitmq_management
ADD run_rabbit.sh /
RUN chmod 755 /run_rabbit.sh
CMD /run_rabbit.sh
