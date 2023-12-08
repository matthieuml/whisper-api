import multiprocessing
import os

try:
    workers = int(os.environ.get("GUNICORN_NB_WORKERS", default=""))
except ValueError:
    # Grab the number of desired workers from the environment or use Ncpu * 2 + 1
    workers = multiprocessing.cpu_count() * 2 + 1
