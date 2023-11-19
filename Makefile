test_run:
	poetry run python3 src/main.py --debug

pylint:
	poetry run pylint src

pylint_tests:
	poetry run pylint tests --disable "missing-function-docstring"

pytest:
	poetry run pytest --tb=no

check: pylint pytest


.PHONY: pylint pylint_tests pytest test_run check