import os

from celery.result import AsyncResult
from flask import Flask

from api.worker.initialization import celery_init_app
from api.worker.tasks import add_together

# =============== Initialize Flask and Celery ===============

app = Flask(__name__)

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
app.config.from_mapping(
    CELERY=dict(
        broker_url=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0",
        result_backend=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0",
        task_ignore_result=True,
    ),
)
celery_app = celery_init_app(app)

# ====================== Define the API ======================


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/add", methods=["GET"])
def start_add() -> dict[str, object]:
    a = 1
    b = 2
    result = add_together.delay(a, b)
    return {"result_id": result.id}


@app.route("/result/<id>", methods=["GET"])
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None,
    }
