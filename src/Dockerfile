# syntax=docker/dockerfile:1

FROM python:3.11.6-bookworm as build-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Pip
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # Poetry
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    # Env
    PYSETUP_PATH="/opt/pysetup"

# Install Poetry
RUN pip install --no-cache-dir poetry==1.6.1

WORKDIR $PYSETUP_PATH

COPY pyproject.toml ./

# Pipefail to ensure build files if something goes wrong
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN poetry install --no-dev --no-root --no-cache

# ====================== RUNTIME ENVIRONMENT ======================
FROM python:3.11.6-slim-bookworm as runtime-base
ENV PYSETUP_PATH="/opt/pysetup" \
    PATH="/opt/pysetup/.venv/bin:$PATH" \
    # Python
    PYTHONUNBUFFERED=1

WORKDIR /src

COPY --from=build-base $PYSETUP_PATH $PYSETUP_PATH

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # install ffmpeg for whisper
    ffmpeg=7:5.1.4-0+deb12u1 \
    && rm -rf /var/lib/apt/lists/*

# ======================== DEV ENVIRONMENT ========================
# `development` image is used during development / testing
FROM runtime-base as development

# Files to start Celery
COPY ./entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r$//g' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# ======================== PROD ENVIRONMENT ========================
# `production` image is used in production
FROM runtime-base as production

COPY . .

# Files to start Celery
RUN sed -i 's/\r$//g' /src/entrypoint.sh \
    && chmod +x /src/entrypoint.sh \
    && rm pyproject.toml poetry.lock Dockerfile

ENTRYPOINT ["/src/entrypoint.sh"]