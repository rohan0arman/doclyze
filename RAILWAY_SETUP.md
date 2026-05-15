# Railway Deployment Setup

This guide helps you deploy Doclyze to Railway with proper OAuth configuration.

## Required Environment Variables

Add these to your Railway project settings:

```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_API_KEY=your-google-api-key
SESSION_SECRET=your-random-secret-key
MAX_FILE_COUNT=5
OAUTH_REDIRECT_URI=https://your-railway-url.up.railway.app/auth/google/callback
```

## Steps

### 1. Get Your Railway URL

In Railway dashboard:
- Go to your Doclyze project
- Check the **Domain** section
- Copy the domain (e.g., `doclyze-production.up.railway.app`)

### 2. Set Environment Variables in Railway

In your Railway project settings → **Variables**:

1. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (from Google Cloud Console)
2. Add `GOOGLE_API_KEY`
3. Add `SESSION_SECRET` (any random 32+ character string)
4. Add `MAX_FILE_COUNT=5`
5. **Most Important**: Add `OAUTH_REDIRECT_URI`:
   ```
   OAUTH_REDIRECT_URI=https://doclyze-production.up.railway.app/auth/google/callback
   ```
   Replace `doclyze-production.up.railway.app` with your actual Railway domain.

### 3. Register Redirect URI in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **Credentials** → Click your OAuth Client ID
4. Add to **Authorized redirect URIs**:
   ```
   https://doclyze-production.up.railway.app/auth/google/callback
   ```

### 4. Deploy

- Commit and push your code to GitHub
- Railway will automatically deploy
- Wait 2-3 minutes for deployment to complete

### 5. Test

1. Go to `https://doclyze-production.up.railway.app`
2. Click **"Login with Google"**
3. You should be redirected to Google's consent screen
4. After approval, you'll be logged in

---

## Troubleshooting

**Error: "redirect_uri_mismatch"**
- Verify `OAUTH_REDIRECT_URI` is set in Railway variables
- Ensure it matches exactly in Google Cloud Console (including https://)
- Clear your browser cache
- Wait for Railway deployment to complete

**Error: "invalid_client"**
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correctly set
- Verify they match your Google Cloud Console credentials
- Make sure not to paste entire credentials.json - set individual values only

**App won't start**
- Check Railway logs for errors
- Verify all required environment variables are set
- Make sure `SESSION_SECRET` is at least 32 characters
