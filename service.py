import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from cleanup import cleanup_old_pastes

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Pastebin Service",
    description="A secure, encrypted pastebin service with CLI integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize the FastAPI application on startup.

    Environment Variables:
        PASTEBIN_BASE_URL: Base URL for the service (default: https://pastebin.marqueewinq.xyz)
        PASTEBIN_DATA_DIR: Directory to store encrypted pastes (default: ./pastes)
        PASTEBIN_KEY_PATH: Path to the secret key file (default: ./secrets/secret.key)

    Raises:
        RuntimeError: If secret key file is not found
        AssertionError: If required shell scripts are missing
    """
    load_dotenv()

    BASE_URL = os.environ.get("PASTEBIN_BASE_URL", "https://pastebin.marqueewinq.xyz")
    DATA_DIR = os.environ.get("PASTEBIN_DATA_DIR", "./pastes")
    KEY_PATH = os.environ.get("PASTEBIN_KEY_PATH", "./secrets/secret.key")
    MAX_AGE_HOURS = os.environ.get("PASTEBIN_MAX_AGE_HOURS", 24)

    logger = logging.getLogger("pastebin")
    logger.info("Starting pastebin service")
    logger.info(f"  BASE_URL: {BASE_URL}")
    logger.info(f"  DATA_DIR: {DATA_DIR}")
    logger.info(f"  KEY_PATH: {KEY_PATH}")
    logger.info(f"  MAX_AGE_HOURS: {MAX_AGE_HOURS}")

    app.state.data_dir = DATA_DIR
    app.state.key_path = KEY_PATH
    app.state.base_url = BASE_URL
    app.state.max_age_hours = MAX_AGE_HOURS
    app.state.templates = Jinja2Templates(directory=str(Path(__file__).parent))

    os.makedirs(app.state.data_dir, exist_ok=True)

    if not os.path.exists(app.state.key_path):
        raise RuntimeError("Secret key not found. Run: ./manage.py secret create")

    with open(app.state.key_path, "rb") as f:
        app.state.fernet = Fernet(f.read())

    app.state.pull_sh_path = os.path.join(os.path.dirname(__file__), "pull.sh")
    app.state.push_sh_path = os.path.join(os.path.dirname(__file__), "push.sh")

    assert os.path.exists(app.state.pull_sh_path), (
        "pull.sh not found at: " + app.state.pull_sh_path
    )
    assert os.path.exists(app.state.push_sh_path), (
        "push.sh not found at: " + app.state.push_sh_path
    )

    with open(app.state.pull_sh_path, "r") as f:
        app.state.pull_sh = f.read()
    with open(app.state.push_sh_path, "r") as f:
        app.state.push_sh = f.read()

    app.state.pull_sh = app.state.pull_sh.replace("<<<base url>>>", app.state.base_url)
    app.state.push_sh = app.state.push_sh.replace("<<<base url>>>", app.state.base_url)

    # Start the periodic cleanup task
    asyncio.create_task(
        periodic_cleanup(
            data_dir=app.state.data_dir,
            max_age_hours=app.state.max_age_hours,
            logger=logger,
        )
    )


async def periodic_cleanup(
    data_dir: str,
    max_age_hours: int = 24,
    logger: logging.Logger = logging.getLogger("pastebin"),
):
    """
    Background task that runs every minute to clean up pastes older than 24 hours.

    This function:
    1. Runs continuously in the background
    2. Checks for pastes older than 24 hours every minute
    3. Deletes expired pastes from the filesystem
    4. Logs cleanup activities for monitoring
    """
    logger.info("Starting periodic cleanup task")
    logger.info(f"  DATA_DIR: {data_dir}")
    logger.info(f"  MAX_AGE_HOURS: {max_age_hours}")

    while True:
        try:
            logger.info("Running periodic cleanup task")
            await cleanup_old_pastes(data_dir, max_age_hours, logger)
            # Wait for 1 minute before next cleanup
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")
            # Wait 5 minutes before retrying if there's an error
            await asyncio.sleep(300)


@app.head("/")
async def head():
    """
    Health check endpoint using HEAD method.
    """
    return Response(status_code=200)


@app.get("/")
async def root(request: Request):
    """
    Main landing page.
    """
    return app.state.templates.TemplateResponse("index.html", {"request": request})


@app.get("/pull.sh")
async def pull(request: Request):
    """
    Serve the pull script for downloading pastes.

    This endpoint returns a bash script that allows users to download
    and decrypt pastes from the command line. The script prompts for
    the paste URL and handles the decryption process.

    Parameters:
        request (Request): FastAPI request object containing request metadata

    Returns:
        Response: Bash script content with text/plain media type

    Usage Examples:

        # Download and execute the script
        curl -s https://pastebin.marqueewinq.xyz/pull.sh | bash

        # Download script to file
        curl -s https://pastebin.marqueewinq.xyz/pull.sh > pull.sh
        chmod +x pull.sh
        ./pull.sh
    """
    return Response(content=app.state.pull_sh, media_type="text/plain")


@app.get("/push.sh")
async def push(request: Request):
    """
    Serve the push script for uploading pastes.

    This endpoint returns a bash script that allows users to upload
    and encrypt content from the command line. The script prompts for
    the content and handles the encryption and upload process.

    Parameters:
        request (Request): FastAPI request object containing request metadata

    Returns:
        Response: Bash script content with text/plain media type

    Usage Examples:

        # Upload content interactively
        curl -s https://pastebin.marqueewinq.xyz/push.sh | bash

        # Upload from file
        curl -s https://pastebin.marqueewinq.xyz/push.sh > push.sh
        chmod +x push.sh
        echo "Hello World" | ./push.sh

        # Upload from stdin
        cat myfile.txt | curl -s https://pastebin.marqueewinq.xyz/push.sh | bash
    """
    return Response(content=app.state.push_sh, media_type="text/plain")


@app.post("/api/v1/paste")
async def create_paste(request: Request, file: UploadFile = File(None)):
    """
    Create a new encrypted paste.

    This endpoint accepts content either as a file upload or as raw data
    in the request body, encrypts it using Fernet encryption, and stores
    it with a unique 12-character ID. The ID is returned for sharing.

    Parameters:
        request (Request): FastAPI request object containing request metadata
        file (UploadFile, optional): File to upload and encrypt. If provided,
                                   takes precedence over request body content.
                                   Defaults to None.

    Request Body:
        Raw text content (if no file is provided)

    Returns:
        Response:
            - Status: 201 Created
            - Content: 12-character paste ID followed by newline
            - Media Type: text/plain

    Raises:
        HTTPException: 400 Bad Request if no data is provided

    Usage Examples:

        # Upload file
        curl -X POST -F "file=@myfile.txt" https://pastebin.marqueewinq.xyz/api/v1/paste

        # Upload raw text
        curl -X POST -d "Hello World" https://pastebin.marqueewinq.xyz/api/v1/paste

        # Upload from stdin
        echo "Hello World" | curl -X POST --data-binary @- https://pastebin.marqueewinq.xyz/api/v1/paste
    """
    body = await request.body()

    if file:
        content = await file.read()
    elif body:
        content = body
    else:
        raise HTTPException(status_code=400, detail="No data provided")

    paste_id = uuid.uuid4().hex[:12]
    enc_data = app.state.fernet.encrypt(content)
    with open(f"{app.state.data_dir}/{paste_id}", "wb") as f:
        f.write(enc_data)

    return Response(content=paste_id + "\n", status_code=201)


@app.get("/api/v1/paste/{paste_id}")
async def get_paste(request: Request, paste_id: str, key: Optional[str] = None):
    """
    Retrieve and decrypt a paste by its ID.

    This endpoint retrieves an encrypted paste from storage, decrypts it
    using the provided key, and returns the original content. The paste ID
    must be exactly 12 characters long and correspond to an existing paste.

    Parameters:
        paste_id (str): 12-character unique identifier for the paste.
                       Must be a valid hexadecimal string.
        key (str, optional): Encryption key for the paste. If provided,
                             the paste will be decrypted using this key.
                             Defaults to None.

    Returns:
        Response:
            - Status: 200 OK
            - Content: Decrypted paste content
            - Media Type: text/plain

    Raises:
        HTTPException:
            - 404 Not Found if paste ID doesn't exist
            - 400 Bad Request if invalid key provided
            - 500 Internal Server Error if decryption fails

    Usage Examples:

        # Retrieve paste content with key
        curl "https://pastebin.marqueewinq.xyz/api/v1/paste/abc123def456?key=your_secret_key"

        # View paste in browser (shows decryption interface)
        # Navigate to: https://pastebin.marqueewinq.xyz/api/v1/paste/abc123def456
    """
    path = f"{app.state.data_dir}/{paste_id}"
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Paste not found")

    if not key:
        return app.state.templates.TemplateResponse(
            "paste.html", {"request": request, "paste_id": paste_id}
        )

    with open(path, "rb") as f:
        enc_data = f.read()

    try:
        data = app.state.fernet.decrypt(enc_data)
    except Exception:
        raise HTTPException(status_code=500, detail="Decryption failed")
    try:
        local_fernet = Fernet(key.encode())
        decrypted_data = local_fernet.decrypt(data)
        return Response(content=decrypted_data, media_type="text/plain")
    except Exception as e:
        # Log the error for debugging
        logging.getLogger("pastebin").error(
            f"Decryption failed for paste {paste_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail="Invalid key or corrupted data")
