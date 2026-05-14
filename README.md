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
- `GOOGLE_CREDENTIALS_JSON` — your OAuth Web App credentials (JSON content, see step 3 below)

**Note:** You no longer need to set `GOOGLE_DRIVE_FOLDER_ID` in the .env file. Instead, paste the folder URL or ID directly in the web interface.

### 3. Set up Google Drive API credentials (OAuth Web App)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Set application type to **Web application** (NOT Desktop App)
6. Add authorized redirect URI: `http://localhost:8000/auth/callback`
7. Download the JSON credentials file
8. **Copy the entire JSON content** and paste it as `GOOGLE_CREDENTIALS_JSON` value in your `.env` file

Example `.env`:
```
GOOGLE_API_KEY=your-gemini-api-key-here
GOOGLE_CREDENTIALS_JSON={"type":"oauth2","client_id":"...","client_secret":"...","redirect_uris":["http://localhost:8000/auth/callback"]}
```

Or if the JSON is multi-line, you can use:
```
GOOGLE_CREDENTIALS_JSON='{"type":"oauth2","client_id":"...","client_secret":"...","redirect_uris":["http://localhost:8000/auth/callback"]}'
```

### 4. Run the application

```bash
uv run python main.py
```

The app will start at `http://127.0.0.1:8000`.

**First time setup:**
1. Open `http://127.0.0.1:8000` in your browser
2. Click **"Authenticate with Google"** button
3. Sign in with your Google account and grant permission to access Google Drive
4. You will be redirected back to the app automatically
5. Your authentication token will be saved for future sessions

**After authentication:**
1. Enter your Google Drive folder URL or ID
2. Click **"Scan & Summarize Documents"**
3. View results and download summaries as CSV/PDF

## Usage

1. Open `http://127.0.0.1:8000` in your browser
2. If this is your first time, click **"Authenticate with Google"** button
3. **Sign in with your Google account** and grant permission to access Drive
4. After authentication, **paste your Google Drive folder URL** (or just the folder ID) into the input box
   - Example URL: `https://drive.google.com/drive/folders/1ABC...`
   - Or just the ID: `1ABC...`
5. Click **"Scan & Summarize Documents"**
6. The app will download all supported files from the folder, extract text, and generate AI summaries using Google Gemini
7. View the results in the styled table
8. Click file names to **download original files**
9. Download all summaries as **CSV** or **PDF** using the buttons below the table

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
