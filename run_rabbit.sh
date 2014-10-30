#!/bin/sh

rabbitmqctl add_user user pass
rabbitmqctl set_permissios user ".*" ".*" ".*"
rabbitmq-server
