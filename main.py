import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from drive import download_all_files
from parser import extract_text
from report import generate_csv, generate_pdf
from summarizer import summarize_text

load_dotenv()

app = FastAPI(title="Doclyze")
templates = Jinja2Templates(directory="templates")

summaries_store: list[dict] = []


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"summaries": summaries_store, "processing": False},
    )


@app.post("/summarize", response_class=HTMLResponse)
async def summarize(request: Request):
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if not folder_id or not openai_key:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "summaries": [],
                "processing": False,
                "error": "Missing GOOGLE_DRIVE_FOLDER_ID or OPENAI_API_KEY in .env",
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
        summary = summarize_text(text, openai_key)
        results.append({"name": f["name"], "summary": summary})

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
        return HTMLResponse("No summaries available. Run summarization first.", status_code=400)

    pdf_bytes = generate_pdf(summaries_store)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=summaries.pdf"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
