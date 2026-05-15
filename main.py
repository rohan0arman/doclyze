import os
import re
import json
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

from drive import download_all_files, authenticate
from parser import extract_text
from report import generate_csv, generate_pdf
from summarizer import summarize_text

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Doclyze")

# Validate OAuth configuration on startup
if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
    raise RuntimeError(
        "ERROR: Missing OAuth credentials!\n"
        "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET as separate environment variables.\n"
        "Do NOT use combined credentials.json - extract client_id and client_secret separately."
    )

# Get max file count from env, default to 5
MAX_FILE_COUNT = int(os.getenv("MAX_FILE_COUNT", "5"))

# OAuth redirect URI (for production deployments, set this explicitly)
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", None)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change-this-secret-key")
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

summaries_store: list[dict] = []

# Configure OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": (
            "openid email profile "
            "https://www.googleapis.com/auth/drive.readonly"
        )
    },
)


def extract_folder_id(url_or_id: str) -> str | None:
    """Extract folder ID from Google Drive URL or return the ID directly."""
    if not url_or_id.strip():
        return None
    
    url_or_id = url_or_id.strip()
    
    # Pattern 1: /folders/FOLDER_ID
    match = re.search(r'/folders/([a-zA-Z0-9-_]+)', url_or_id)
    if match:
        return match.group(1)
    
    # Pattern 2: id=FOLDER_ID parameter
    match = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url_or_id)
    if match:
        return match.group(1)
    
    # If it's just an ID (no URL), return as-is
    if re.match(r'^[a-zA-Z0-9-_]{20,}$', url_or_id):
        return url_or_id
    
    return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Check if user is authenticated
    token = request.session.get("google_token")
    needs_auth = not token
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "summaries": summaries_store,
            "processing": False,
            "error": None,
            "needs_auth": needs_auth
        },
    )


@app.get("/login/google")
async def login_google(request: Request):
    """Start Google OAuth flow."""
    # Use explicit redirect_uri if set (for production), otherwise auto-detect
    if OAUTH_REDIRECT_URI:
        redirect_uri = OAUTH_REDIRECT_URI
    else:
        redirect_uri = request.url_for("auth_google_callback")
    
    return await oauth.google.authorize_redirect(
        request,
        str(redirect_uri),
        access_type="offline",
        prompt="consent",
    )


@app.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    """Handle Google OAuth callback."""
    try:
        token = await oauth.google.authorize_access_token(request)
        request.session["google_token"] = token
        return RedirectResponse(url="/")
    except Exception as e:
        return HTMLResponse(
            f"<h1>Authentication Failed</h1><p>Error: {str(e)}</p><a href='/'>Go back</a>",
            status_code=400
        )


@app.post("/summarize", response_class=HTMLResponse)
async def summarize(request: Request, folder_input: str = Form(...)):
    # Check authentication first
    token_data = request.session.get("google_token")
    if not token_data:
        return RedirectResponse(url="/login/google")
    
    google_key = os.getenv("GOOGLE_API_KEY", "")

    if not google_key:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "summaries": [],
                "processing": False,
                "error": "Missing GOOGLE_API_KEY in .env",
                "needs_auth": False
            },
        )
    
    # Extract folder ID from URL or use directly if it's an ID
    folder_id = extract_folder_id(folder_input)
    
    if not folder_id:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "summaries": [],
                "processing": False,
                "error": "Invalid folder URL or ID. Please enter a valid Google Drive folder URL or ID.",
                "needs_auth": False
            },
        )

    files = download_all_files(folder_id, token_data, max_files=MAX_FILE_COUNT)
    if not files:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "summaries": [],
                "processing": False,
                "error": "No supported documents found in the specified folder.",
                "needs_auth": False
            },
        )

    results = []
    for f in files:
        text = extract_text(f["path"])
        summary = summarize_text(text, google_key)
        results.append({
            "name": f["name"], 
            "summary": summary,
            "path": f["path"],
            "file_id": len(results)
        })

    summaries_store.clear()
    summaries_store.extend(results)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"summaries": results, "processing": False, "needs_auth": False},
    )


@app.get("/download/csv")
async def download_csv():
    if not summaries_store:
        return HTMLResponse("No summaries available. Run summarization first.", status_code=400)

    csv_content = generate_csv(summaries_store)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=summaries.csv"},
    )


@app.get("/download/pdf")
async def download_pdf():
    if not summaries_store:
        return HTMLResponse(
            "No summaries available. Run summarization first.",
            status_code=400
        )

    pdf_bytes = generate_pdf(summaries_store)

    return StreamingResponse(
        iter([bytes(pdf_bytes)]),   # FIX
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=summaries.pdf"
        },
    )


@app.get("/download/file/{file_id}")
async def download_file(file_id: int):
    if file_id < 0 or file_id >= len(summaries_store):
        return HTMLResponse("File not found.", status_code=404)
    
    file_path = summaries_store[file_id].get("path")
    if not file_path or not os.path.exists(file_path):
        return HTMLResponse("File not found on server.", status_code=404)
    
    file_name = os.path.basename(file_path)
    
    def iterfile():
        with open(file_path, mode="rb") as file:
            yield from file
    
    return StreamingResponse(
        iterfile(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
