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

pytest:
	poetry run pytest -k "basic"

pytest-extended:
	poetry run pytest


check: pylint flake8 pytest


.PHONY: pylint pylint_tests pylint-no-todo pytest test_run check flake8