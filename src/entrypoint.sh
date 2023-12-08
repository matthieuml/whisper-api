#!/bin/sh

echo "Redis is running"

echo "Starting celery..."
celery -A api.app.celery_app worker --loglevel=warning --logfile=/var/log/celery.log --detach
echo "Celery is running with log level warning"

echo "Starting server..."

exec "$@"