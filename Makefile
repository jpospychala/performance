build:
	docker build -t m1 .

server: build
	docker run -d -p 5672:5672 -p 15672:15672 --name m1test1 m1

.PHONY: server build
