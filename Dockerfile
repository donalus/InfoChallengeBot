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
    apk add cargo gcc g++ libffi-dev patchelf

###############################################
# Builder Image
###############################################
FROM python-base as builder-base

RUN apk add curl git

# Install all Python requirements
RUN curl -sSL https://install.python-poetry.org | python3 -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --without dev

###############################################
# Production Image
###############################################
FROM builder-base as production

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
RUN echo $VENV_PATH
RUN . $VENV_PATH/bin/activate


COPY . /app
WORKDIR /app
RUN chmod +x ./docker-entrypoint.sh
#CMD tail -f /dev/null

ENTRYPOINT ./docker-entrypoint.sh $0 $@
CMD [ "poetry ", "run", "python", "bot.py" ]
##CMD tail -f /dev/null
