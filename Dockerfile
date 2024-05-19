# Use an official Python base image
FROM python:3.10-bullseye

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

RUN mkdir /app/
RUN mkdir /.cache/ && chown -R 1000:1000 /.cache/
WORKDIR /app

ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY Makefile .
COPY poetry.lock .
COPY pyproject.toml .
COPY readme.md .
COPY src src

RUN apt update && apt install -y p7zip-full rsync && rm -rf /var/lib/apt/lists/* && apt-get clean
RUN pip install poetry

RUN chmod -R 755 /app

USER 1000
RUN poetry install

CMD ["poetry", "run", "python3", "src/main.py"]
