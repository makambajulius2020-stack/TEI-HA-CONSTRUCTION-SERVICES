# OAuth Setup Guide

This guide explains how to configure Google and Microsoft/Outlook OAuth sign-in for the TEI-HA AI Tools.

## Prerequisites

1. Python backend server running
2. OAuth credentials from Google and Microsoft

## Step 1: Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API** and **People API**
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Choose **Web application** as the application type
6. Add authorized redirect URIs:
   - `http://localhost:5500/ai-tools.html` (for local development)
   - `https://yourdomain.com/ai-tools.html` (for production)
7. Copy the **Client ID** and **Client Secret**

## Step 2: Microsoft/Outlook OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Set the application name (e.g., "TEI-HA AI Tools")
5. Set redirect URI:
   - Platform: **Web**
   - URI: `http://localhost:5500/ai-tools.html` (for local development)
   - Add production URI: `https://yourdomain.com/ai-tools.html`
6. Click **Register**
7. Go to **Certificates & secrets** → **New client secret**
8. Copy the **Application (client) ID** and **Client secret value**

## Step 3: Configure Environment Variables

Create a `.env` file in the `backend` directory or set environment variables:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here

# Frontend URL (adjust for your environment)
FRONTEND_URL=http://localhost:5500
```

Or set them in your system environment variables.

## Step 4: Install Dependencies

Make sure you have the required packages installed:

```bash
pip install -r requirements.txt
```

The OAuth dependencies (`authlib` and `python-jose`) are already included in `requirements.txt`.

## Step 5: Restart Backend Server

After setting the environment variables, restart your backend server:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Or use the startup script:

```bash
start-backend.bat  # Windows
./start-backend.sh  # Linux/Mac
```

## How It Works

1. User clicks "Google" or "Outlook" button on the login form
2. Frontend requests OAuth URL from backend
3. User is redirected to Google/Microsoft login page
4. After authentication, user is redirected back to `ai-tools.html` with an authorization code
5. Frontend sends the code to backend callback endpoint
6. Backend exchanges code for access token and retrieves user info
7. Backend creates/updates user account and returns user email
8. Frontend stores user email and signs the user in

## Testing

1. Make sure backend server is running
2. Open `ai-tools.html` in your browser
3. Click "Sign In" button
4. Click "Google" or "Outlook" button
5. You should be redirected to the OAuth provider's login page
6. After logging in, you should be redirected back and signed in

## Troubleshooting

### "OAuth is not configured" Error

- Make sure environment variables are set correctly
- Restart the backend server after setting environment variables
- Check that variable names match exactly (case-sensitive)

### Redirect URI Mismatch

- Ensure the redirect URI in OAuth provider settings matches exactly
- Check that `FRONTEND_URL` environment variable is set correctly
- For Google: Redirect URI should be `http://localhost:5500/ai-tools.html` (no query parameters)
- For Microsoft: Same as Google

### CORS Errors

- Make sure CORS is enabled in the backend (already configured)
- Check that frontend URL matches the `FRONTEND_URL` environment variable

## Security Notes

- Never commit `.env` files or credentials to version control
- Use environment variables or secure secret management in production
- Keep client secrets secure and rotate them regularly
- Use HTTPS in production

