###############################################
# Base Image
###############################################
FROM python:3.9-alpine AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.0a2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="${POETRY_HOME}/bin:$VENV_PATH/bin:$PATH"

# These are required for the pycord[speed] extensions
RUN apk update && apk upgrade && \
    apk add --no-cache --virtual .build-deps cargo gcc g++ libffi-dev patchelf curl git

###############################################
# Builder Image
###############################################
FROM python-base as builder-base

# These are required for connecting to different databases with sqlalchemy
RUN apk add --no-cache mariadb-connector-c-dev

# Install all Python requirements (requires version 1.20.0a2 or better)
RUN curl -sSL https://install.python-poetry.org | python3 - --preview

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY ../poetry.lock ../pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --without dev,utils,docs

###############################################
# Production Image
###############################################
FROM builder-base as production

# Copy over the built python libraries
COPY --from=builder-base $VENV_PATH $VENV_PATH
# Make the image smaller by removing build-deps
RUN apk del .build-deps

WORKDIR /app

# Copying in the entrypoint
COPY ./docker/docker-entrypoint.sh /opt/docker/docker-entrypoint.sh
RUN chmod +x /opt/docker/docker-entrypoint.sh

# Make an empty data director for sqlite
RUN mkdir data

COPY /src .
COPY .env ./

ENTRYPOINT /opt/docker/docker-entrypoint.sh $0 $@
CMD ["python", "bot.py"]
# CMD ["sh", "while true; do sleep 1; echo '.'; done;"]