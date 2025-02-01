# Whisper API

A lightweight API for Whisper transcription, featuring a queue system with Celery. Designed primarily for API calls, it also includes a simple web interface, and a Flower dashboard is provided for monitoring Celery tasks.

## Project Structure
```
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
|   ├── entrypoint.sh
│   ├── guniconf.py
│   ├── poetry.lock
│   └── pyproject.toml
├── .pre-commit-config.yaml
├── docker-compose-prod.yaml
├── docker-compose.yaml
├── LICENSE
└── README.md
```

## Getting Started

### Prerequisites

Ensure you have [Docker](https://docs.docker.com/engine/install/) installed. For GPU acceleration, it is highly recommended to install the [NVIDIA Container Runtime](https://docs.docker.com/config/containers/resource_constraints/#gpu).

### Setup

1. Clone the repository
   ```sh
   git clone git@github.com:matthieuml/whisper-api.git
   ```
2. Create an environment file
   
   A template `.env-example` is provided. Copy it to `.env` in the root directory and update the values as needed.

   For security reasons, it is recommended to modify these values.
   
   Adjust `WORKER_CONCURRENCY` based on your GPU’s VRAM and the memory requirements of your tasks to prevent failures due to insufficient memory.
3. Build and start the Docker containers
   ```sh
   docker compose -f docker-compose-prod.yaml up
   ```

Once running, the API will be available at `http://localhost:8000`, and the Celery dashboard (Flower) will be accessible at `http://localhost:5555`.

## Development

### Environment

To work with the development environment and apply changes to the API, use the following command:
```sh
docker compose -f docker-compose.yaml up
```

The app will automatically update on every change without requiring a server restart.

### Tests

To run the tests after starting the container, use this command:
```sh
docker compose exec -T <api-container> python -m pytest api/tests/test.py
```

### Linting

This project uses [pre-commit](https://pre-commit.com/) to automatically lint the code. To set up the hooks, run:
```sh
pre-commit install
```

The hooks will be executed automatically on every commit to ensure code quality.
