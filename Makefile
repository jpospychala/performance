build:
	docker build -t m1 .

rabbitmq_server:
	docker run -d -p 5672:5672 -p 15672:15672 --name m1test1 m1

clean:
	docker stop m1test1

.PHONY: rabbitmq_server build clean
