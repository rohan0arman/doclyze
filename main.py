import os
import re
import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from drive import download_all_files
from parser import extract_text
from report import generate_csv, generate_pdf
from summarizer import summarize_text

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Doclyze")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

summaries_store: list[dict] = []


creds_raw = os.getenv("GOOGLE_CREDENTIALS_JSON")

if not creds_raw:
    raise RuntimeError("GOOGLE_CREDENTIALS_JSON missing")

try:
    creds = json.loads(creds_raw)
except json.JSONDecodeError:
    raise RuntimeError("Invalid GOOGLE_CREDENTIALS_JSON")

Path("credentials.json").write_text(json.dumps(creds))


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
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"summaries": summaries_store, "processing": False, "error": None},
    )


@app.post("/summarize", response_class=HTMLResponse)
async def summarize(request: Request, folder_input: str = Form(...)):
    google_key = os.getenv("GOOGLE_API_KEY", "")

    if not google_key:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "summaries": [],
                "processing": False,
                "error": "Missing GOOGLE_API_KEY in .env",
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
            },
        )

    files = download_all_files(folder_id)
    if not files:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "summaries": [],
                "processing": False,
                "error": "No supported documents found in the specified folder.",
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
            "file_id": len(results)  # Simple ID for file reference
        })

    summaries_store.clear()
    summaries_store.extend(results)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"summaries": results, "processing": False},
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
