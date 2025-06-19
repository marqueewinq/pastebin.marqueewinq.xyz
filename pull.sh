#!/bin/bash

set -e

BASE_URL=<<<base url>>>
PASTE_URL="${BASE_URL}/api/v1/paste"

check_dep() {
    printf "checking for %s... " "$1"
    if eval "$2" >/dev/null 2>&1; then
        echo "ok"
    else
        echo "missing"
        echo "Command failed: $2"
        echo "$3"
        exit 1
    fi
}

check_dep "python3" "python3 --version" "Install python3 with: sudo apt install python3"
check_dep "fernet" "python3 -c 'from cryptography.fernet import Fernet'" "Install fernet with: pip install cryptography"

if [ -t 0 ]; then
    read -rp "Paste URL: " url
else
    echo "Paste URL:" >&2
    read -r url < /dev/tty
fi

# Strip whitespace and newlines from URL
url=$(echo "$url" | tr -d '\n\r\t' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

IFS='#' read -r paste_url key <<< "$url"

if [[ -z "$paste_url" || -z "$key" ]]; then
    echo "Invalid URL. Format: ${PASTE_URL}/<id>#<key>"
    exit 1
fi

data=$(curl -sf "$paste_url") || {
    echo "Failed to fetch paste"
    exit 1
}

echo "--------------------------------"
echo "    Decrypted content below"
echo "--------------------------------"

FERNET_KEY="$key" python3 -c "
from cryptography.fernet import Fernet
import sys, os
key = os.environ['FERNET_KEY'].encode()
cipher = Fernet(key)
dec = cipher.decrypt(sys.stdin.buffer.read())
sys.stdout.buffer.write(dec)
" <<< "$data"
