CERIT_DOCKER_REPOSITORY_NAME=ivetastrnadova

test_run:
	poetry run python3 src/main.py --debug

black:
	poetry run black src

pylint:
	poetry run pylint src

pylint-no-todo:
	poetry run pylint src --disable "fixme"

pylint-tests:
	poetry run pylint tests --disable "missing-function-docstring"

flake8:
	poetry run flake8 src

docker-tests:
	docker-compose -f tests/docker-compose.yaml build
	docker-compose -f tests/docker-compose.yaml up

docker:
	docker-compose build
	docker-compose up --force-recreate --remove-orphans

pytest:
	poetry run pytest -k "not integration"

pytest-integration:
	poetry run pytest -m "integration"

pytest-coverage:
	poetry run pytest --cov=src

# builds docker image with name pdb-data-cruncher and tag "latest"
docker-build:
	docker build -t cerit.io/${CERIT_DOCKER_REPOSITORY_NAME}/pdb-data-cruncher .

docker-push:
	docker push cerit.io/${CERIT_DOCKER_REPOSITORY_NAME}/pdb-data-cruncher


check: pylint flake8 pytest


.PHONY: pylint pylint_tests pylint-no-todo pytest test_run check flake8 docker-tests