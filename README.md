# 🔐 Secure Pastebin - End-to-End Encrypted Text Sharing

A privacy-focused pastebin service with true end-to-end encryption. Your data is encrypted on your device before being uploaded, and the encryption key is never stored on our servers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com/)

## 🌟 Features

- **🔒 True End-to-End Encryption**: Data is encrypted locally before upload
- **🚀 Simple CLI Tools**: Easy-to-use bash scripts for upload/download
- **⚡ Fast & Lightweight**: Built with FastAPI for high performance
- **🕐 Auto-Expiry**: Encrypted data automatically deleted after 24 hours
- **🌐 Zero-Knowledge**: Server never sees your plaintext content
- **📱 No Accounts**: No registration or personal data required
- **🔧 Open Source**: Full transparency and self-hostable

## 🏗️ Architecture

This service implements a **double-encryption model**:

1. **Client-Side Encryption**: Users encrypt content locally using Fernet encryption
2. **Server-Side Encryption**: Server adds an additional encryption layer for storage
3. **Secure Key Sharing**: Encryption keys are shared via side channels (URL fragments)

### Security Flow

```
Client Device          Server              Recipient Device
     │                    │                       │
     │ Plaintext          │                       │
     │ 🔑 Generate Key    │                       │
     │ 🔒 Encrypt         │                       │
     │ ──HTTPS──>         │                       │
     │                    │ 🔒 Store Encrypted    │
     │                    │ 🔐 Add Server Key     │
     │                    │ 🔒🔒 Double Encrypted │
     │                    │ ──HTTPS──>            │
     │                    │                       │ 🔒 Download Encrypted
     │                    │                       │ 🔑 Use Shared Key
     │                    │                       │ 🔓 Decrypt
     │                    │                       │ Plaintext
```

## 🚀 Quick Start

### Using the CLI Tools

**Upload content:**
```bash
curl -s https://pastebin.marqueewinq.xyz/push.sh | bash
```

**Download and decrypt:**
```bash
curl -s https://pastebin.marqueewinq.xyz/pull.sh | bash
```

### Manual API Usage

**Upload encrypted content:**
```bash
# Encrypt and upload
echo "Hello World" | python3 -c "
import sys, requests
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
data = sys.stdin.buffer.read()
encrypted = cipher.encrypt(data)
r = requests.post('https://pastebin.marqueewinq.xyz/api/v1/paste', data=encrypted)
paste_id = r.text.strip()
print(f'https://pastebin.marqueewinq.xyz/api/v1/paste/{paste_id}#{key.decode()}')
"
```

**Download and decrypt:**
```bash
# Download and decrypt
curl -s "https://pastebin.marqueewinq.xyz/api/v1/paste/abc123def456" | \
python3 -c "
from cryptography.fernet import Fernet
import sys
key = 'your_secret_key_here'.encode()
cipher = Fernet(key)
decrypted = cipher.decrypt(sys.stdin.buffer.read())
sys.stdout.buffer.write(decrypted)
"
```

## 🛠️ Installation & Deployment

### Prerequisites

- Python 3.8+
- Docker (optional)
- `cryptography` library

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/marqueewinq/pastebin.marqueewinq.xyz.git
cd pastebin.marqueewinq.xyz
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create server-side secret key:**
```bash
python manage.py secret create
```

4. **Set environment variables** (in `.env` file):
```bash
export PASTEBIN_BASE_URL="https://your-domain.com"
export PASTEBIN_DATA_DIR="./pastes"
export PASTEBIN_KEY_PATH="./secrets/secret.key"
export PASTEBIN_MAX_AGE_HOURS=24
```

5. **Run the service:**
```bash
python manage.py service run
```

### Docker Deployment

1. **Build and run with Docker Compose:**
```bash
docker-compose up -d
```

2. **Or build manually:**
```bash
docker build -t secure-pastebin .
docker run -p 8000:8000 -v $(pwd)/pastes:/app/pastes secure-pastebin
```

## 📚 API Documentation

See docs:

 - [OpenAPI](https://pastebin.marqueewinq.xyz/docs)
 - [ReDoc](https://pastebin.marqueewinq.xyz/redoc)

### API Examples

**Upload content:**
```bash
# File upload
curl -X POST -F "file=@myfile.txt" https://pastebin.marqueewinq.xyz/api/v1/paste

# Raw text
curl -X POST -d "Hello World" https://pastebin.marqueewinq.xyz/api/v1/paste

# From stdin
echo "Hello World" | curl -X POST --data-binary @- https://pastebin.marqueewinq.xyz/api/v1/paste
```

**Download encrypted content:**
```bash
curl https://pastebin.marqueewinq.xyz/api/v1/paste/abc123def456
```

## 🔐 Security Model

### Encryption Details

- **Algorithm**: Fernet (AES-128 in CBC mode with PKCS7 padding)
- **Key Generation**: Cryptographically secure random keys
- **Key Storage**: Never stored on server, shared via URL fragments
- **Transmission**: All data transmitted over HTTPS
- **Storage**: Double-encrypted on server (client + server keys)

### Security Guarantees

- ✅ **Zero-Knowledge**: Server cannot decrypt your content
- ✅ **End-to-End**: Only you and your recipients can decrypt
- ✅ **Forward Secrecy**: Each paste uses a unique key
- ✅ **No Metadata**: No logs of who accessed what
- ✅ **Auto-Expiry**: Data automatically deleted after 24 hours

### Threat Model

This service protects against:
- **Server compromise**: Server cannot decrypt your content
- **Network interception**: All traffic is HTTPS encrypted
- **Storage compromise**: Data is encrypted at rest
- **Metadata collection**: No user accounts or tracking

**Not protected against:**
- **Key compromise**: If your key is leaked, content is compromised
- **Side-channel attacks**: Timing attacks, etc.
- **Client-side malware**: Malware on your device can access keys


## 🤝 Contributing

Contributions are welcome. Submit a pull request or an issue if you want to add or fix anything.


## 📄 License

This project is licensed under the MIT License.

---

**⚠️ Security Notice**: This service is designed for secure text sharing but should not be used for highly sensitive information. Always verify the authenticity of the service and use additional security measures when appropriate.

This software is provided as is, with no warranty. Use at your own risk.
