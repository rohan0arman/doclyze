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

# Optional: Set explicit redirect URI for OAuth (useful when behind proxies)
# If not set, the app will auto-detect from request URL
# Format: https://your-railway-domain.up.railway.app/auth/google/callback
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", None)

# Add custom middleware to handle Railway's reverse proxy headers
# This custom approach is more reliable than ProxyFixMiddleware for Railway
class RailwayProxyFixMiddleware:
    """Middleware to fix URL scheme when behind Railway's reverse proxy."""
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Railway sends X-Forwarded-Proto and X-Forwarded-Host headers
            # We need to trust these to construct the correct URL
            headers = dict(scope.get("headers", []))
            
            # Check for Railway's forwarded headers
            forwarded_proto = headers.get(b"x-forwarded-proto", b"").decode().lower()
            forwarded_host = headers.get(b"x-forwarded-host", b"").decode()
            
            if forwarded_proto and forwarded_host:
                scope["scheme"] = forwarded_proto
                scope["server"] = (forwarded_host.split(":")[0], 443 if forwarded_proto == "https" else 80)
                print(f"🔌 Railway proxy detected: scheme={forwarded_proto}, host={forwarded_host}")
            
            # Also check X-Forwarded-For for client IP
            forwarded_for = headers.get(b"x-forwarded-for", b"").decode()
            if forwarded_for:
                scope["client"] = (forwarded_for.split(",")[0].strip(), 0)
        
        await self.app(scope, receive, send)

# Add custom Railway proxy middleware FIRST
app.add_middleware(RailwayProxyFixMiddleware)

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
    # Use explicit redirect_uri if set, otherwise auto-detect from request
    if OAUTH_REDIRECT_URI:
        redirect_uri = OAUTH_REDIRECT_URI
        print(f"🔐 Using explicit OAUTH_REDIRECT_URI from env: {redirect_uri}")
    else:
        redirect_uri = request.url_for("auth_google_callback")
    
    # CRITICAL DEBUG: Show what's being sent to Google
    print("\n" + "="*70)
    print("🔐 OAUTH LOGIN INITIATED")
    print("="*70)
    print(f"Redirect URI: {redirect_uri}")
    print(f"Request URL scheme: {request.url.scheme}")
    print(f"Request URL hostname: {request.url.hostname}")
    print(f"Request headers:")
    for key, value in request.headers.items():
        if "forward" in key.lower() or "host" in key.lower() or "proto" in key.lower():
            print(f"  {key}: {value}")
    print("="*70 + "\n")
    
    # IMPORTANT: Verify the redirect_uri is HTTPS for production
    if not str(redirect_uri).startswith("https://") and "localhost" not in str(redirect_uri):
        print(f"⚠️  WARNING: Non-HTTPS redirect_uri detected in production!")
        print(f"   This will cause 'redirect_uri_mismatch' error with Google")
        print(f"   Current: {redirect_uri}")
        print(f"   Solution: Set OAUTH_REDIRECT_URI env variable to correct HTTPS URL\n")
    
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
        # Debug: Log incoming callback
        print(f"🔐 OAuth Callback: received from {request.url}")
        print(f"   Query params: {dict(request.query_params)}")
        
        token = await oauth.google.authorize_access_token(request)
        request.session["google_token"] = token
        print("✅ OAuth Token stored in session")
        return RedirectResponse(url="/")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ OAuth Error: {error_msg}")
        return HTMLResponse(
            f"<h1>Authentication Failed</h1><p>Error: {error_msg}</p><a href='/'>Go back</a>",
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
