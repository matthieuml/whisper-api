import json
import os
import time

from celery.result import AsyncResult
from flask import Flask, flash, redirect, render_template, request
from werkzeug.utils import secure_filename

from api.utils import allowed_extensions
from api.worker.initialization import celery_init_app
from api.worker.tasks import transcribe_audio

# =============== Initialize Flask and Celery ===============

app = Flask(__name__)

# Load the configuration from the environment variables
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
app.config.from_mapping(
    CELERY=dict(
        broker_url=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0",
        result_backend=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0",
        task_ignore_result=True,
    ),
)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["UPLOAD_FOLDER"] = "/src/api/files/"
ALLOWED_EXTENSIONS = {"mp4", "mp3", "wav", "flac"}

celery_app = celery_init_app(app)

# ====================== Define the API ======================


@app.route("/")
def root():
    return render_template("index.html")


@app.route("/transcribe", methods=["GET", "POST"])
def load_and_transcribe() -> dict[str, object]:
    if request.method == "POST":
        # Check if the post request has a file
        if "file" not in request.files:
            flash("No file part!")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename
        if file.filename == "":
            flash("No file selected!")
            return redirect(request.url)
        if not allowed_extensions(file.filename, ALLOWED_EXTENSIONS):
            flash("File extension not allowed!")
            return redirect(request.url)
        # Ensure the filename is safe (no directory traversal)
        # and add timestamp to handle multiple save with same name
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename_with_timestamp = f"{timestamp}-{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename_with_timestamp)
        file.save(file_path)
        result = transcribe_audio.delay(full_audio=file_path)
        return redirect("/result/" + result.id)
    return render_template("transcribe.html")


@app.route("/result/<id>", methods=["GET"])
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    response_data = {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None,
    }
    return json.dumps(response_data, ensure_ascii=False)
