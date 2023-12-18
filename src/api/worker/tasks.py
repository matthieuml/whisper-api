import os
import torch
import whisper
from celery import shared_task


@shared_task(ignore_result=False)
def transcribe_audio(full_audio):
    # Define model before the try block
    model = None
    try:
        model = whisper.load_model(name="small", download_root="/src/api/models")
        result = model.transcribe(full_audio)
        # Delete model and clear GPU memory
        if model is not None:
            del model
        torch.cuda.empty_cache()
    except torch.cuda.OutOfMemoryError:
        # Delete model and clear GPU memory
        if model is not None:
            del model
        torch.cuda.empty_cache()
        # Raise exception
        raise Exception("Currently not enough GPU memory to load the model.")
    except Exception as e:
        raise e
    # Delete the file
    os.remove(full_audio)
    return result["text"]
