IS_RABBIT_DOCKER_BUILT := $(shell docker images | grep rabbit_docker >/dev/null 2>&1 && echo "yes" || echo "no")
ifeq ($(IS_RABBIT_DOCKER_BUILT),yes)
rabbit_docker_image:
else
rabbit_docker_image: rabbit_docker_image_build
endif

rabbit_docker_image_build:
	docker build -t rabbit_docker docker
	docker run -d -p 5672:5672 -p 15672:15672 --name rabbit_docker rabbit_docker
	sleep 10

.PHONY: rabbit_docker_image rabbit_docker_image_build
