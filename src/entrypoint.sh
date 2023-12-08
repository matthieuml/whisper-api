#!/bin/sh

echo "Redis is running"

echo "Starting celery..."
celery -A api.app.celery_app worker --loglevel=info --logfile=/var/log/celery.log --detach
echo "Celery is running"

echo "Starting server..."

exec "$@"