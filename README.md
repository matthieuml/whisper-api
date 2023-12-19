# Whisper API

Small API for Whisper transcription with a queue system using Celery. It is meant to be used with API calls, but a simple web interface is also available.

## Project Structure
```
├── compose
│   └── docker-compose.yaml
|   └── docker-compose-prod.yaml
├── src
│   ├── api
│   │   ├── files
│   │   ├── models
│   │   ├── templates
|   |   |   └── index.html
|   |   |   └── transcribe.html
│   │   ├── tests
│   │   |   └── test.py
│   │   ├── worker
│   │   |   └── initialization.py
│   │   |   └── tasks.py
│   │   ├── app.py
│   │   └── utils.py
│   ├── Dockerfile
│   ├── guniconf.py
│   ├── poetry.lock
│   └── pyproject.toml
├── .pre-commit-config.yaml
└── README.md
```

## Getting Started

### Prerequisites

You must have [Docker](https://docs.docker.com/engine/install/) installed on your machine, and it is strongly recommended to have [NVIDIA Container Runtime](https://docs.docker.com/config/containers/resource_constraints/#gpu) to have GPU support.

### Setup

1. Clone the repo
   ```sh
   git clone git@github.com:matthieuml/whisper-api.git
   ```
2. Create an environment file `.env` in the `compose/` directory
   ```sh
   SECRET_KEY=secret
   REDIS_HOST=redis
   REDIS_PASSWORD=password
   GUNICORN_NB_WORKERS=4
   WORKER_CONCURRENCY=2
   ```
   
   They are technically some default values, but you should change some of them for security reasons.

   The number of worker concurrency should be adjusted depending on the VRAM size of your GPU, and the memory requirement of your task. Otherwise, a task might fail due to a lack of memory.
2. Build and run the Docker image
   ```sh
   docker-compose -f compose/docker-compose-prod.yaml up
   ```

The API should be accessible at `localhost:8000` or `0.0.0.0:8000`.

## Development

### Environment

If you want to make some changes to the API, you can use the development environment with the command:
```sh
docker-compose -f compose/docker-compose.yaml up
```

The app will be recompiled on every change, and the server will be restarted.

### Tests

You can run the tests after starting the container with the command:
```sh
docker-compose exec -T worker python -m pytest api/tests/test.py
```

### Linting

This project uses [pre-commit](https://pre-commit.com/) to lint the code. You can install it with the command:
```sh
pip install pre-commit
```

Then, you can install the hooks with the command:
```sh
pre-commit install
```

The hooks will be then run on every commit.
