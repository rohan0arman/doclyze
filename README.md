# Doclyze - Document Summarizer via Google Drive

A simple application that connects to a Google Drive folder, downloads documents (PDF, DOCX, TXT), and uses Google's Gemini AI model to generate summaries for each document. Results are displayed on a web interface and can be downloaded as CSV or PDF reports.

## Tech Stack

- **Python 3.13** with [uv](https://docs.astral.sh/uv/) package manager
- **FastAPI** for the web interface
- **LangChain + Google Gemini** for AI-powered summarization
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

- `GOOGLE_API_KEY` — your Google AI Studio API key (get it from https://aistudio.google.com/apikey)

**Note:** You no longer need to set `GOOGLE_DRIVE_FOLDER_ID` in the .env file. Instead, paste the folder URL or ID directly in the web interface.

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
2. **Paste your Google Drive folder URL** (or just the folder ID) into the input box
   - Example URL: `https://drive.google.com/drive/folders/1ABC...`
   - Or just the ID: `1ABC...`
3. Click **"Scan & Summarize Documents"**
4. The app will download all supported files from the folder, extract text, and generate AI summaries using Google Gemini
5. View the results in the styled table
6. Download summaries as **CSV** or **PDF** using the buttons below the table

## Supported File Types

| Format | Library Used |
|--------|-------------|
| PDF    | PyMuPDF     |
| DOCX   | python-docx |
| TXT    | Built-in    |
| XLSX   | openpyxl    |
| XLS    | xlrd        |
| CSV    | Built-in    |
| MD     | Built-in    |

Google Docs files in the folder are automatically exported as PDF before processing.

## Project Structure

```
doclyze/
├── main.py          # FastAPI app and routes
├── drive.py         # Google Drive OAuth2 and file operations
├── parser.py        # Document text extraction
├── summarizer.py    # LangChain + Google Gemini summarization
├── report.py        # CSV and PDF report generation
├── templates/
│   └── index.html   # Web interface
├── .env.example     # Environment variables template
├── pyproject.toml   # Project config and dependencies
└── README.md
```

## Requirements Fulfilled

✅ **Google Drive Integration:**
- OAuth2 authentication implemented
- Dynamic folder selection via URL or ID input
- Download documents from specified folder

✅ **Document Parsing:**
- Extract text from PDF files (PyMuPDF)
- Extract text from DOCX files (python-docx)
- Extract text from TXT files (built-in)

✅ **Summarization:**
- Uses Google Gemini AI model (gemini-2.0-flash)
- Generates 5-10 sentence summaries
- Handles large documents via chunking

✅ **Output Interface:**
- Modern FastAPI web application
- Responsive HTML/CSS interface
- Real-time processing feedback

✅ **Download Options:**
- CSV report export
- PDF report export
- Styled HTML table display with file names and summaries
