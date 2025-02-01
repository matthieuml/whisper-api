import os
from typing import List, Optional

import requests
import torch
import whisper
from celery import shared_task

from api.worker.utils import format_response


@shared_task(ignore_result=False)
def transcribe_audio(
    file_path: str,
    model: str = "small",
    language: Optional[str] = None,
    response_format: str = "json",
    temperature: Optional[float] = None,
    timestamp_granularities: List[str] = ["segment"],
    callback_url: Optional[str] = None,
) -> dict:
    try:
        # Load model
        model = whisper.load_model(model, download_root="/src/api/models")

        # Prepare transcription options
        options = {
            "task": "transcribe",
            "language": language,
            "temperature": temperature if temperature is not None else 0,
            "word_timestamps": "word" in timestamp_granularities,
        }

        # Run transcription
        result = model.transcribe(file_path, **options)

        # Format response based on response_format
        response = format_response(result, response_format, file_path)

        # If callback_url is provided, send the response
        if callback_url:
            try:
                headers = {"Content-Type": "application/json"}
                if response_format in ["text", "srt", "vtt"]:
                    # For text-based formats, send the text content directly
                    payload = {
                        "text": response["text"],
                        "format": response_format,
                        "filename": response["filename"],
                    }
                else:
                    # For JSON formats, send the full response
                    payload = response

                requests.post(
                    callback_url, json=payload, headers=headers
                ).raise_for_status()
            except Exception as e:
                print(f"Callback to {callback_url} failed: {str(e)}")

        # Cleanup
        os.remove(file_path)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return response

    except Exception as e:
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise e
