import os
import time
from io import StringIO

from celery.result import AsyncResult
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from api.utils import allowed_extensions, download_file
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


@app.route("/v1/audio/transcriptions", methods=["POST"])
def transcribe() -> dict[str, object]:
    """OpenAI-compatible endpoint with advanced features"""
    file_path = None

    try:
        # Check if we received a file or URL
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            if not allowed_extensions(file.filename, ALLOWED_EXTENSIONS):
                return jsonify({"error": "File extension not allowed"}), 400

            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            filename_with_timestamp = f"{timestamp}-{filename}"
            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"], filename_with_timestamp
            )
            file.save(file_path)

        elif "file" in request.form:
            url = request.form["file"]
            if not url:
                return jsonify({"error": "No URL provided"}), 400

            # Download file from URL
            file_path = download_file(url, app.config["UPLOAD_FOLDER"])
        else:
            return jsonify({"error": "No file or URL provided"}), 400

        # Get other form parameters
        model = request.form.get("model", "small")
        language = request.form.get("language", None)
        response_format = request.form.get("response_format", "json")
        temperature = (
            float(request.form.get("temperature"))
            if "temperature" in request.form
            else None
        )
        timestamp_granularities = request.form.getlist("timestamp_granularities") or [
            "segment"
        ]
        callback_url = request.form.get("callback_url")

        # Start transcription task
        result = transcribe_audio.delay(
            file_path=file_path,
            model=model,
            language=language,
            response_format=response_format,
            temperature=temperature,
            timestamp_granularities=timestamp_granularities,
            callback_url=callback_url,
        )

        # If callback_url is provided, return immediately
        if callback_url:
            return jsonify(
                {
                    "status": "processing",
                    "message": "Transcription will be sent to callback URL when complete",
                }
            )

        # Otherwise, wait for result as before
        task_result = result.get()

        # Handle different response formats
        if response_format in ["text", "srt", "vtt"]:
            output = StringIO(task_result["text"])
            return send_file(
                output,
                mimetype=task_result["content_type"],
                as_attachment=True,
                download_name=task_result["filename"],
            )

        return jsonify(task_result)

    except Exception as e:
        # Clean up downloaded file if there was an error
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 400


@app.route("/v0/audio/transcriptions", methods=["POST"])
def front_transcribe() -> dict[str, object]:
    """Legacy endpoint that returns simple text transcription"""
    file_path = None

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_extensions(file.filename, ALLOWED_EXTENSIONS):
            return jsonify({"error": "File extension not allowed"}), 400

        # Save file with timestamp
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename_with_timestamp = f"{timestamp}-{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename_with_timestamp)
        file.save(file_path)

        # Use the transcribe_audio task with text format for backward compatibility
        result = transcribe_audio.delay(
            file_path=file_path, model="small", response_format="text"
        )
        return redirect(url_for("task_result", id=result.id))

    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 400


@app.route("/v1/audio/transcriptions/result/<id>", methods=["GET"])
def task_result(id: str) -> dict[str, object]:
    """Legacy endpoint for getting task results"""
    result = AsyncResult(id)
    if result.ready():
        if result.successful():
            return jsonify({"status": "completed", "result": result.result["text"]})
        else:
            return jsonify({"status": "failed", "error": str(result.result)}), 500
    else:
        return jsonify({"status": "processing"}), 202
