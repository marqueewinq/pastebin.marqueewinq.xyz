#!/bin/bash
set -e

# Create secret key if it doesn't exist
if [ ! -f "/app/secrets/secret.key" ]; then
    echo "Creating secret key..."
    python manage.py secret create
else
    echo "Secret key already exists."
fi

# Start the service
echo "Starting pastebin service..."
exec python manage.py service run --host 0.0.0.0 --port 8050 