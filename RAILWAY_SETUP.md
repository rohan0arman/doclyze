# Railway Environment Configuration Guide

## OAuth Configuration Issue

The error `401: invalid_client` means Railway doesn't have the correct OAuth credentials. 

### ❌ WRONG (Current Setup):
```
CREDENTIALS_JSON={"web": {"client_id": "...", "client_secret": "...", ...}}
```

### ✅ CORRECT (Required):
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## How to Extract Credentials from credentials.json

1. **Download credentials.json from Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Select your project
   - Go to "Credentials"
   - Download your OAuth 2.0 Client ID (Web application)

2. **Open the credentials.json file and find**:
```json
{
  "web": {
    "client_id": "12345-abcdef.apps.googleusercontent.com",
    "client_secret": "your_secret_here",
    "redirect_uris": ["http://localhost:8000/auth/google/callback"],
    ...
  }
}
```

3. **Extract these two values and set them as Railway env variables**:
   - `GOOGLE_CLIENT_ID` → `client_id` value
   - `GOOGLE_CLIENT_SECRET` → `client_secret` value

---

## Required Railway Environment Variables

Add these in your Railway project settings:

```
GOOGLE_CLIENT_ID=<extracted from credentials.json>
GOOGLE_CLIENT_SECRET=<extracted from credentials.json>
GOOGLE_API_KEY=<your Google API key with Gemini access>
SESSION_SECRET=<generate a random secret, min 32 chars>
MAX_FILE_COUNT=5
```

### Important Notes:
- ⚠️ **Do NOT paste entire credentials.json** - set the individual values only
- ⚠️ **Redirect URI must match**: Your Railway URL must be registered in Google Cloud Console
  - If Railway gives you: `https://doclyze-prod.railway.app`
  - Add to Google Cloud Console Authorized redirect URIs: `https://doclyze-prod.railway.app/auth/google/callback`

---

## Session Secret Generation

Generate a secure random key (on your local machine):

**Windows PowerShell**:
```powershell
$bytes = [byte[]]::new(32)
[System.Security.Cryptography.RNGCryptoServiceProvider]::new().GetBytes($bytes)
$secret = [Convert]::ToBase64String($bytes)
Write-Host $secret
```

**Linux/Mac**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and set as `SESSION_SECRET` in Railway.

---

## Verify Configuration

After setting env variables in Railway:
1. Redeploy your application
2. Go to your Railway URL
3. Click "Login with Google"
4. You should be redirected to Google consent screen
5. After approval, you should be logged in

If you still see 401 error:
- Check Railway logs for the exact error
- Verify redirect URI matches exactly in Google Cloud Console
- Clear browser cache and try again
