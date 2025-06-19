#!/bin/bash

set -e

BASE_URL="https://pastebin.marqueewinq.xyz"
PASTE_URL="${BASE_URL}/api/v1/paste"

check_dep() {
    printf "checking for %s... " "$1"
    if "$2" &>/dev/null; then
        echo "ok"
    else
        echo "missing"
        echo "$3"
        exit 1
    fi
}

check_dep "python3" "command -v python3" "Install python3 with: \n\tsudo apt install python3"
check_dep "fernet" "python3 -c 'from cryptography.fernet import Fernet'" "Install fernet with: \n\tpip install cryptography"

if [ -t 0 ]; then
    read -rp "Paste URL: " url
else
    read -r url
fi

IFS='#' read -r paste_url key <<< "$url"

if [[ -z "$paste_url" || -z "$key" ]]; then
    echo "Invalid URL. Format: ${PASTE_URL}/<id>#<key>"
    exit 1
fi

data=$(curl -sf "$paste_url") || {
    echo "Failed to fetch paste"
    exit 1
}

python3 -c "
from cryptography.fernet import Fernet
import sys
key = b'$key'
cipher = Fernet(key)
dec = cipher.decrypt(sys.stdin.buffer.read())
sys.stdout.buffer.write(dec)
" <<< "$data"
