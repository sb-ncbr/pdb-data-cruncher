# Work in progress

The whole project is under active development and will undergo major
changes.

## Local running (work in progress)

Package management is done via [poetry](https://python-poetry.org/). If run locally (without Docker),
you need to have poetry installed and on a path, and run `poetry install` before proceeding with running it.

Run pylint (static syntax checker)
```bash
poetry run pylint src
```

Run pytest (unit tests)
```bash
poetry run pytest --tb=no
```