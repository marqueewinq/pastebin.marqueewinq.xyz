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

read -r -d '' PYTHON_SCRIPT <<'EOF'
import sys, requests
from cryptography.fernet import Fernet
PASTE_URL = "${PASTE_URL}"

def main():
    key = Fernet.generate_key()
    cipher = Fernet(key)

    data = sys.stdin.buffer.read()
    encrypted = cipher.encrypt(data)

    r = requests.post(f"{PASTE_URL}", data=encrypted)
    if r.status_code != 201:
        sys.stderr.write(f"Upload failed: {r.status_code} {r.text}\n")
        sys.exit(1)

    paste_id = r.text.strip()
    print(f"{PASTE_URL}/{paste_id}#{key.decode()}")

if __name__ == "__main__":
    main()
EOF

if [ -t 0 ]; then
    echo "Enter your secret (Ctrl+D to finish):"
fi

python3 -c "$PYTHON_SCRIPT"
