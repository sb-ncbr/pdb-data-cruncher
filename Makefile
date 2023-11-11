test_run:
	poetry run mulsan --debug

pylint:
	poetry run pylint src

pylint_tests:
	poetry run pylint tests --disable "missing-function-docstring"

pytest:
	poetry run pytest --tb=no

check: pylint pytest


.PHONY: pylint pylint_tests pytest test_run check