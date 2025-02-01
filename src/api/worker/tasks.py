import os
import requests
from typing import Optional, List

import torch
import whisper
from celery import shared_task

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
                        "filename": response["filename"]
                    }
                else:
                    # For JSON formats, send the full response
                    payload = response

                requests.post(callback_url, json=payload, headers=headers).raise_for_status()
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

def format_response(result: dict, response_format: str, file_path: str) -> dict:
    filename_noext, _ = os.path.splitext(os.path.basename(file_path))

    if response_format == "text":
        return {
            "text": result["text"].strip(),
            "content_type": "text/plain",
            "filename": f"{filename_noext}.txt"
        }

    elif response_format == "json":
        return {
            "text": result["text"].strip()
        }

    elif response_format == "verbose_json":
        response = {
            "task": "transcribe",
            "duration": result["segments"][-1]["end"] if result["segments"] else 0,
            "text": result["text"].strip(),
        }

        if result.get("word_timestamps", False):
            response["words"] = [
                {
                    "word": word["word"].strip(),
                    "start": word["start"],
                    "end": word["end"]
                }
                for segment in result["segments"]
                for word in segment.get("words", [])
            ]
        else:
            response["segments"] = [
                {
                    "id": i,
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                }
                for i, segment in enumerate(result["segments"])
            ]
        return response

    elif response_format in ["srt", "vtt"]:
        if response_format == "srt":
            return {
                "text": format_srt(result["segments"]),
                "content_type": "text/srt; charset=utf-8",
                "filename": f"{filename_noext}.srt"
            }
        else:
            return {
                "text": format_vtt(result["segments"]),
                "content_type": "text/vtt; charset=utf-8",
                "filename": f"{filename_noext}.vtt"
            }

def format_srt(segments: List[dict]) -> str:
    def srt_time(t):
        return "{:02d}:{:02d}:{:06.3f}".format(
            int(t//3600), int(t//60)%60, t%60
        ).replace(".", ",")

    return "\n".join([
        f"{i}\n{srt_time(segment['start'])} --> {srt_time(segment['end'])}\n{segment['text'].strip()}\n"
        for i, segment in enumerate(segments, 1)
    ])

def format_vtt(segments: List[dict]) -> str:
    def vtt_time(t):
        return "{:02d}:{:06.3f}".format(int(t//60), t%60)

    return "\n".join(
        ["WEBVTT\n"] + [
            f"{vtt_time(segment['start'])} --> {vtt_time(segment['end'])}\n{segment['text'].strip()}\n"
            for segment in segments
        ]
    )
