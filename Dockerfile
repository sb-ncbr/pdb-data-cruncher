FROM python:3.10-bullseye

WORKDIR /app/

COPY Makefile .
COPY poetry.lock .
COPY pyproject.toml .
COPY readme.md .
COPY src src

RUN apt update && apt install -y p7zip-full
RUN pip install poetry
RUN poetry install
CMD ["poetry", "run", "python3", "src/main.py"]
#CMD tail -f /dev/null