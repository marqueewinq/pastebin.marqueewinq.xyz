#!/usr/bin/env python3
import os, click, uvicorn
from cryptography.fernet import Fernet

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.getenv("PASTEBIN_DATA_DIR", "./pastes")
SECRETS_DIR = os.getenv("PASTEBIN_SECRETS_DIR", "./secrets")
KEY_PATH = os.path.join(SECRETS_DIR, "secret.key")


@click.group()
def cli():
    pass


@cli.group()
def service():
    """Manage the pastebin service."""
    pass


@service.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
def run(host: str = "0.0.0.0", port: int = 8000):
    """Run the pastebin FastAPI server."""
    uvicorn.run("service:app", host=host, port=port)


@cli.group()
def secret():
    """Manage encryption keys."""
    pass


@secret.command()
@click.option("--force", is_flag=True, help="Force overwrite existing key")
def create(force: bool = False):
    """Generate a new secret key."""
    os.makedirs(SECRETS_DIR, exist_ok=True)
    if os.path.exists(KEY_PATH):
        if not force:
            click.confirm("Key already exists. Overwrite?", abort=True)
        else:
            os.remove(KEY_PATH)
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    os.chmod(KEY_PATH, 0o600)
    click.echo("Secret key generated.")


if __name__ == "__main__":
    cli()
