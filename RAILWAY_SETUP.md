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
OAUTH_REDIRECT_URI=https://doclyze-production.up.railway.app/auth/google/callback
```

### Important Notes:
- ⚠️ **Do NOT paste entire credentials.json** - set the individual values only
- ⚠️ **OAUTH_REDIRECT_URI must match exactly** what's in Google Cloud Console
  - Format: `https://your-railway-url/auth/google/callback`
  - Must use HTTPS, not HTTP
  - No trailing slash

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

---

## Troubleshooting: Error 400: redirect_uri_mismatch

### The Problem
Railway uses a reverse proxy and typically sends `X-Forwarded-Proto: https` headers, but these weren't being properly trusted. The app was constructing `http://` URLs instead of `https://`, causing Google to reject the redirect.

### The Solution (Updated)
The app now includes:
1. **Custom RailwayProxyFixMiddleware** - Properly reads Railway's `X-Forwarded-Proto` and `X-Forwarded-Host` headers
2. **OAUTH_REDIRECT_URI environment variable** - Explicitly set the redirect URI (recommended as the most reliable approach)

### Step-by-Step Fix

**1. Find Your Railway URL**
- Go to Railway dashboard
- Select your Doclyze project
- Copy the production domain (e.g., `doclyze-production.up.railway.app`)

**2. Set OAUTH_REDIRECT_URI in Railway**
In your Railway project settings, add:
```
OAUTH_REDIRECT_URI=https://doclyze-production.up.railway.app/auth/google/callback
```
⚠️ Replace `doclyze-production.up.railway.app` with your actual Railway domain
⚠️ Must be HTTPS, not HTTP

**3. Verify Google Cloud Console Settings**
Confirm these Authorized Redirect URIs are set:
```
https://doclyze-production.up.railway.app/auth/google/callback
http://localhost:8000/auth/google/callback
http://127.0.0.1:8000/auth/google/callback
```

**4. Redeploy**
- Commit and push code
- Railway will auto-deploy
- Wait 2-3 minutes for deployment

**5. Test the Login**
1. Go to `https://doclyze-production.up.railway.app`
2. Click "Login with Google"
3. Check Railway logs - you should see:
   ```
   🔐 Using explicit OAUTH_REDIRECT_URI from env: https://doclyze-production.up.railway.app/auth/google/callback
   ```

### If You Still Get redirect_uri_mismatch
1. **Check the exact redirect_uri in error message**
   - Copy it from the error page
   - Compare with what's in Google Cloud Console Authorized redirect URIs
   - They must match exactly (including https:// and /auth/google/callback)

2. **Clear browser cache**
   - Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
   - Delete all cookies for doclyze-production.up.railway.app

3. **Check Railway logs**
   - Go to Railway dashboard → Deployments → View logs
   - Look for:
     ```
     ⚠️  WARNING: Non-HTTPS redirect_uri detected in production!
     ```
   - If you see this, OAUTH_REDIRECT_URI is not set correctly

4. **Verify environment variables in Railway**
   - Go to Railway Variables tab
   - Confirm OAUTH_REDIRECT_URI is set to the HTTPS URL
   - Make sure there are no typos or extra spaces

### How It Works
- When you click "Login with Google", the app checks for `OAUTH_REDIRECT_URI` env variable
- If set, it uses that exact URL (most reliable)
- If not set, it auto-detects from the request using the custom middleware
- The app logs everything for debugging
