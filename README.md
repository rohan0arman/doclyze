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

### 2. Configure Google Drive API OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Add authorized redirect URIs:
     - `http://localhost:8000/auth/google/callback`
     - `http://127.0.0.1:8000/auth/google/callback`
     - (For production: `https://your-domain.com/auth/google/callback`)
5. Copy your **Client ID** and **Client Secret**

### 3. Set environment variables

Copy and fill in `.env`:

```bash
cp .env.example .env
```

Edit `.env` with:

```env
# Google OAuth credentials (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Google API key (for Gemini access)
GOOGLE_API_KEY=your-api-key

# Session secret for security (any random string, min 32 chars)
SESSION_SECRET=your-random-secret

# Maximum files to process per folder (default: 5)
MAX_FILE_COUNT=5

# OAuth redirect URI (set for production deployments)
OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### 4. Get Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Get API Key**
3. Copy and paste into `.env` as `GOOGLE_API_KEY`

## Running the Application

### Local Development

```bash
uv run python main.py
```

The app will start at `http://127.0.0.1:8000`.

**First time setup:**
1. Open `http://127.0.0.1:8000` in your browser
2. Click **"Login with Google"** button
3. Sign in with your Google account and grant permission to access Google Drive
4. You'll be redirected back to the app automatically
5. Your authentication token is saved for future sessions

**After authentication:**
1. Paste a Google Drive folder URL or ID
2. Click **"Scan & Summarize Documents"**
   - Processes up to `MAX_FILE_COUNT` files (default: 5)
   - Skips unsupported file types
3. View results and download summaries as CSV/PDF

### Production Deployment (Railway, etc.)

When deploying to production:

1. Set `OAUTH_REDIRECT_URI` to your production URL:
   ```env
   OAUTH_REDIRECT_URI=https://your-domain.com/auth/google/callback
   ```

2. Register the redirect URI in Google Cloud Console:
   - Go to Credentials → OAuth Client
   - Add to **Authorized redirect URIs**:
     ```
     https://your-domain.com/auth/google/callback
     ```

3. Set all required environment variables in your hosting platform (Railway, etc.)

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
