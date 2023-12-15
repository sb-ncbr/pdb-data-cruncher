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

## Logging levels philosophy

- `EXCEPTION` - Something broke in a way I did not expect. The highest severity, needs to be investigated 
  as it is not supposed to happen. It most likely means the code logic is flawed.
- `ERROR` - There is a serious issue with processing the data. Most likely means big chunk of protein data is 
  missing, corrupted or otherwise wrong and cannot be processed. It should be noted and kept eye on during the next
  program run, investigated if needed.
- `WARNING` - Minor data issue (e.g. few non-critical values missing). Or situation that does not create problem for
  the code at all, but may be weird (e.g. multiple values of something where only one is expected). It may be good to 
  review this level occassionally. It will not be spamed - minor issues get aggregated and logged only once on this 
  level (and then in more defail on INFO level).
- `INFO` - Information about important milestones in code execution or detailed information about minor issues.
  May get cluttered, it is worth to search through it only when looking for something specific.
- `DEBUG` - More detail about the code execution, tasks started, configuration loaded, number of things processed, etc.
  Should be completely turned off for normal running.


## Code quality ensurances

- `pylint` and `flake8` are good packages for pointing out bad practises, missing documentation or other 
  deviations from PEP8 code style. Occasionally, when exceptions make sense, 'pylint: disable=xxx' or 'noqa=xxx' 
  comments are used to silence them. They only report their findings, manual changes are needed.
- `black` is a code formatter. Running it will reformat the code to follow one fo the code styles. Great to use when
  unusure of how to make the code in python most readable. (It is good to follow it for unififed look of code and 
  better readability.) It can fix a lot of issues pointed out by pylint/flake8 automatically.