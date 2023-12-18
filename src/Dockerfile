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
    PATH="/opt/pysetup/.venv/bin:$PATH"

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

# Avoid creating __pycache__ directories
# that copies into the host in development
ENV PYTHONDONTWRITEBYTECODE=1

# ======================== PROD ENVIRONMENT ========================
# `production` image is used in production
FROM runtime-base as production

# Create a user to run the app as non-root
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    fablab

COPY . .

# Give the right permission to the user
RUN chown -R fablab:fablab /src \
    && touch /var/log/celery.log /var/log/gunicorn.log \
    && chown fablab:fablab /var/log/celery.log /var/log/gunicorn.log \
    && rm pyproject.toml poetry.lock Dockerfile

USER fablab