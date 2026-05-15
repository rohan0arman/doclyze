import io
import os
import tempfile

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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


def authenticate(token_data: dict):
    """Create Credentials object from OAuth token data."""
    if not token_data:
        raise Exception("User not authenticated. No token data provided.")
    
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return creds


def list_files(service, folder_id: str, max_files: int = 5) -> list[dict]:
    """List supported files inside a Google Drive folder.
    
    Args:
        service: Google Drive API service
        folder_id: Folder ID to list files from
        max_files: Maximum number of files to return (default: 5 to limit API costs)
    
    Returns:
        List of supported files, limited to max_files count
    """
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
            # Stop once we reach max_files to control costs
            if len(supported) >= max_files:
                break
    
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


def download_all_files(folder_id: str, token_data: dict, max_files: int = 5) -> list[dict]:
    """Download supported files from a Google Drive folder.

    Args:
        folder_id: Google Drive folder ID
        token_data: OAuth token data from session
        max_files: Maximum number of files to download (default: 5 to limit API costs)

    Returns a list of dicts with keys: name, path, mime.
    """
    creds = authenticate(token_data)
    service = build("drive", "v3", credentials=creds)

    files = list_files(service, folder_id, max_files=max_files)
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
