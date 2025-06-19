from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import Response
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import uuid, os


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    load_dotenv()

    BASE_URL = os.environ.get("PASTEBIN_BASE_URL", "https://pastebin.marqueewinq.xyz")
    DATA_DIR = os.environ.get("PASTEBIN_DATA_DIR", "./pastes")
    KEY_PATH = os.environ.get("PASTEBIN_KEY_PATH", "./secrets/secret.key")

    app.state.data_dir = DATA_DIR
    app.state.key_path = KEY_PATH
    app.state.base_url = BASE_URL

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


@app.get("/pull.sh")
async def pull(request: Request):
    """
    Script to pull a paste from the pastebin.

    To use with: `curl -s https://pastebin.marqueewinq.xyz/pull.sh | bash`

    The script will prompt for the paste URL with secret key.
    """
    return Response(content=app.state.pull_sh, media_type="text/plain")


@app.get("/push.sh")
async def push(request: Request):
    """
    Script to push a paste to the pastebin.

    To use with: `curl -s https://pastebin.marqueewinq.xyz/push.sh | bash`

    The script will prompt for secret key and the paste content.
    """
    return Response(content=app.state.push_sh, media_type="text/plain")


@app.post("/api/v1/paste")
async def create_paste(request: Request, file: UploadFile = File(None)):
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
async def get_paste(paste_id: str):
    path = f"{app.state.data_dir}/{paste_id}"
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Paste not found")
    with open(path, "rb") as f:
        enc_data = f.read()
    try:
        data = app.state.fernet.decrypt(enc_data)
    except:
        raise HTTPException(status_code=500, detail="Decryption failed")
    return Response(content=data, media_type="text/plain")
