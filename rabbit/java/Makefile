rabbit_docker_image:
	cd .. && make rabbit_docker_image

startdocker:
	docker start rabbit_docker
	sleep 10

stopdocker:
	docker stop rabbit_docker

mvncleaninstall:
	mvn clean install

.PHONY: rabbit_docker_image mvncleaninstall
