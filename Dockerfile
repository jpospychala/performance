FROM ubuntu:14.04
MAINTAINER jacek.pospychala@gmail.com

RUN echo deb http://www.rabbitmq.com/debian/ testing main >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install --force-yes -y rabbitmq-server
RUN rabbitmq-plugins enable rabbitmq_management

CMD rabbitmq-server
