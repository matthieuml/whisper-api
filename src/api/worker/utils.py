import os
from typing import List


def format_response(result: dict, response_format: str, file_path: str) -> dict:
    filename_noext, _ = os.path.splitext(os.path.basename(file_path))

    if response_format == "text":
        return {
            "text": result["text"].strip(),
            "content_type": "text/plain",
            "filename": f"{filename_noext}.txt",
        }

    elif response_format == "json":
        return {"text": result["text"].strip()}

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
                    "end": word["end"],
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
                "filename": f"{filename_noext}.srt",
            }
        else:
            return {
                "text": format_vtt(result["segments"]),
                "content_type": "text/vtt; charset=utf-8",
                "filename": f"{filename_noext}.vtt",
            }


def format_srt(segments: List[dict]) -> str:
    def srt_time(t):
        return "{:02d}:{:02d}:{:06.3f}".format(
            int(t // 3600), int(t // 60) % 60, t % 60
        ).replace(".", ",")

    return "\n".join(
        [
            f"{i}\n{srt_time(segment['start'])} --> {srt_time(segment['end'])}\n{segment['text'].strip()}\n"
            for i, segment in enumerate(segments, 1)
        ]
    )


def format_vtt(segments: List[dict]) -> str:
    def vtt_time(t):
        return "{:02d}:{:06.3f}".format(int(t // 60), t % 60)

    return "\n".join(
        ["WEBVTT\n"]
        + [
            f"{vtt_time(segment['start'])} --> {vtt_time(segment['end'])}\n{segment['text'].strip()}\n"
            for segment in segments
        ]
    )
