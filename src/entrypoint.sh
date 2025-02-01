#!/bin/sh

# Give the whisper-worker user ownership of the files and models directories
chown -R whisper-worker:whisper-group /src/api/files /src/api/models && chmod -R 775 /src/api/files /src/api/models

# Start worker process as whisper-worker user
exec runuser -u whisper-worker -- "$@"