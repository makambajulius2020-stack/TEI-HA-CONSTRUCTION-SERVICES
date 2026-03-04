# Environment Variables Setup

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your actual values

3. **The server will automatically load** `.env` file on startup

## Environment Variables

### Database
- `CHAT_DB_PATH` - Path to SQLite database file (default: `chat.db`)

### N8N Integration (Optional)
- `N8N_WEBHOOK_URL` - Webhook URL for N8N automation (optional)

### Email Configuration (Optional)
- `ADMIN_EMAIL` - Admin email address for notifications
- `SMTP_HOST` - SMTP server hostname (e.g., `smtp.gmail.com`)
- `SMTP_PORT` - SMTP server port (default: `587`)
- `SMTP_USER` - SMTP username/email
- `SMTP_PASS` - SMTP password or app password
- `SMTP_FROM` - From email address (defaults to SMTP_USER)

### OAuth Configuration (Optional)
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `MICROSOFT_CLIENT_ID` - Microsoft OAuth client ID
- `MICROSOFT_CLIENT_SECRET` - Microsoft OAuth client secret
- `FRONTEND_URL` - Frontend URL for OAuth redirects (default: `http://localhost:5500`)

## Gmail Setup (for SMTP)

If using Gmail:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Create an app password for "Mail"
   - Use this password in `SMTP_PASS` (not your regular password)

3. Update `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASS=your-16-char-app-password
   SMTP_FROM=your-email@gmail.com
   ```

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to version control
- `.env` is already in `.gitignore`
- Use `.env.example` as a template
- Keep your secrets secure!

## Testing

After setting up `.env`, restart the backend server:
```bash
python launcher.py
```

The server will automatically load all environment variables from `.env`.

