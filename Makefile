test_run:
	poetry run mulsan

pylint:
	poetry run pylint src

pylint_tests:
	poetry run pylint tests --disable "missing-function-docstring"

pytest:
	poetry run pytest --tb=no


.PHONY: pylint pylint_tests pytest