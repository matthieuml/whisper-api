import multiprocessing
import os

# Grab the number of desired workers from the environment or use Ncpu * 2 + 1
workers = os.environ.get(
    "GUNICORN_NB_WORKERS",
    multiprocessing.cpu_count() * 2 + 1,
)
