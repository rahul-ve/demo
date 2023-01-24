
POSTGRES_USER := $(shell pass show db/postgres_docker_default_un)
POSTGRES_PASSWORD := $(shell pass show db/postgres_docker_default_pw)

export POSTGRES_USER
export POSTGRES_PASSWORD


.ONESHELL:


.PHONY: container_up
container_up:
	docker-compose -f ./postgres_adminer.yaml up -d



.PHONY: container_down
container_down:
	docker-compose -f ./postgres_adminer.yaml down