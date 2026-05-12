# Doclyze - Document Summarizer via Google Drive

A simple application that connects to a Google Drive folder, downloads documents (PDF, DOCX, TXT), and uses OpenAI GPT to generate summaries for each document. Results are displayed on a web interface and can be downloaded as CSV or PDF reports.

## Tech Stack

- **Python 3.13** with [uv](https://docs.astral.sh/uv/) package manager
- **FastAPI** for the web interface
- **LangChain + OpenAI** for AI-powered summarization
- **Google Drive API** with OAuth2 authentication
- **PyMuPDF / python-docx** for document parsing
- **FPDF2** for PDF report generation

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/rohan0arman/doclyze.git
cd doclyze
uv sync
```

### 2. Configure environment variables

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env` and set:

- `OPENAI_API_KEY` — your OpenAI API key
- `GOOGLE_DRIVE_FOLDER_ID` — the ID of the Google Drive folder to scan (from the folder URL)

### 3. Set up Google Drive API credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Set application type to **Desktop App**
6. Download the JSON file and save it as `credentials.json` in the project root

### 4. Run the application

```bash
uv run python main.py
```

The app will start at `http://127.0.0.1:8000`.

On the first run, a browser window will open for Google OAuth authentication. After granting access, a `token.json` file will be saved locally so you don't need to re-authenticate each time.

## Usage

1. Open `http://127.0.0.1:8000` in your browser
2. Click **"Scan & Summarize Documents"**
3. The app will download all supported files from the configured Drive folder, extract text, and generate AI summaries
4. View the results in the styled table
5. Download summaries as **CSV** or **PDF** using the buttons below the table

## Supported File Types

| Format | Library Used |
|--------|-------------|
| PDF    | PyMuPDF     |
| DOCX   | python-docx |
| TXT    | Built-in    |

Google Docs files in the folder are automatically exported as PDF before processing.

## Project Structure

```
doclyze/
├── main.py          # FastAPI app and routes
├── drive.py         # Google Drive OAuth2 and file operations
├── parser.py        # Document text extraction
├── summarizer.py    # LangChain + OpenAI summarization
├── report.py        # CSV and PDF report generation
├── templates/
│   └── index.html   # Web interface
├── .env.example     # Environment variables template
├── pyproject.toml   # Project config and dependencies
└── README.md
```
