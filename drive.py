import io
import os
import tempfile

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

SUPPORTED_MIMES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "text/markdown": ".md",
    "text/x-markdown": ".md",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
}

# Google Docs/Sheets/Slides are online-only; export them as PDF
EXPORT_MIMES = {
    "application/vnd.google-apps.document": (
        "application/pdf",
        ".pdf",
    ),
}


def authenticate():
    """Run OAuth2 flow and return credentials."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return creds


def list_files(service, folder_id: str) -> list[dict]:
    """List supported files inside a Google Drive folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = (
        service.files()
        .list(q=query, fields="files(id, name, mimeType)")
        .execute()
    )
    files = results.get("files", [])

    supported = []
    for f in files:
        mime = f["mimeType"]
        if mime in SUPPORTED_MIMES or mime in EXPORT_MIMES:
            supported.append(f)
    return supported


def download_file(service, file_meta: dict, dest_dir: str) -> str:
    """Download a single file to dest_dir. Returns local file path."""
    file_id = file_meta["id"]
    name = file_meta["name"]
    mime = file_meta["mimeType"]

    if mime in EXPORT_MIMES:
        export_mime, ext = EXPORT_MIMES[mime]
        request = service.files().export_media(
            fileId=file_id, mimeType=export_mime
        )
        if not name.endswith(ext):
            name += ext
    else:
        request = service.files().get_media(fileId=file_id)

    local_path = os.path.join(dest_dir, name)
    with open(local_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return local_path


def download_all_files(folder_id: str) -> list[dict]:
    """Authenticate, list, and download all supported files.

    Returns a list of dicts with keys: name, path, mime.
    """
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    files = list_files(service, folder_id)
    if not files:
        return []

    dest_dir = tempfile.mkdtemp(prefix="doclyze_")
    downloaded = []
    for f in files:
        path = download_file(service, f, dest_dir)
        downloaded.append(
            {"name": f["name"], "path": path, "mime": f["mimeType"]}
        )

    return downloaded
