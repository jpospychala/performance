rabbit_docker_image:
	docker build -t rabbit_docker docker
	docker run -d -p 5672:5672 -p 15672:15672 --name rabbit_docker rabbit_docker

.PHONY: rabbit_docker_image
