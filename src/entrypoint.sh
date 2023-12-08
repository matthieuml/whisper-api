#!/bin/sh

echo "Starting celery..."
celery -A app.celery_app worker --loglevel=info --logfile=/var/log/celery.log --detach
echo "Celery started"

echo "Starting server..."

exec "$@"