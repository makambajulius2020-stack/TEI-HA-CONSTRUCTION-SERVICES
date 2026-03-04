import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

import httpx
import africastalking
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from authlib.integrations.httpx_client import AsyncOAuth2Client
from difflib import SequenceMatcher


DB_PATH = os.getenv("CHAT_DB_PATH", os.path.join(os.path.dirname(__file__), "chat.db"))
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")  # e.g., http://localhost:5678/webhook/your-id
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "artsrock099@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "no-reply@teiha.local")

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")

# Africa's Talking Configuration
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY = os.getenv("AT_API_KEY", "")

# Initialize Africa's Talking
try:
    africastalking.initialize(AT_USERNAME, AT_API_KEY)
    at_payments = africastalking.Payment
    print(f"✅ Africa's Talking initialized: {AT_USERNAME}")
except Exception as e:
    print(f"⚠️ Africa's Talking init failed (test mode): {e}")
    at_payments = None

def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                prompts_used INTEGER NOT NULL DEFAULT 0,
                chars_used INTEGER NOT NULL DEFAULT 0,
                welcome_sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Subscriptions table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                email TEXT NOT NULL,
                tier TEXT NOT NULL, -- free | pro | max
                cycle TEXT NOT NULL, -- week | month | year
                currency TEXT NOT NULL, -- UGX | USD
                status TEXT NOT NULL, -- active | canceled | past_due
                current_period_end TEXT NOT NULL,
                provider TEXT NOT NULL, -- stripe | flutterwave
                provider_customer_id TEXT,
                provider_sub_id TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (email)
            )
            """
        )
        # Ensure usage window column exists for 24h reset
        try:
            cur.execute("ALTER TABLE users ADD COLUMN window_started_at TEXT")
        except Exception:
            pass
        # Initialize missing window_started_at to now
        try:
            cur.execute("UPDATE users SET window_started_at = ? WHERE window_started_at IS NULL", (datetime.utcnow().isoformat(),))
        except Exception:
            pass
        conn.commit()
    finally:
        conn.close()


ensure_db()

app = FastAPI(title="TEI-HA Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ====== Company Knowledge Base (lightweight) ======
COMPANY_PROFILE = {
    "name": "TEI-HA Construction Services Ltd",
    "tagline": "Quality is our priority",
    "location": "Nansana - Wakiso, Uganda",
    "email": "teihaconstructionservices@gmail.com",
    "services": [
        "AI-Powered Design",
        "Architecture Design",
        "Interior Design",
        "Project Management",
        "Construction Services",
    ],
    "ai_tools": [
        "Budget Sensei",
        "Inspiration Sketch Pad",
        "Style Fusion",
        "Virtual Site Scout",
    ],
    "plans": {
        "free": "Free plan with limited requests.",
        "pro": "Pro plan, typically UGX 35,000 per month (local demo pricing).",
        "max": "Max plan, typically UGX 95,000 per month (local demo pricing).",
    },
    "payments": [
        "MTN Mobile Money",
        "Airtel Money",
        "Cards (coming soon)",
    ],
    "social": {
        "youtube": "https://www.youtube.com/@Tei-haConstructionServices",
    },
}

FAQ_ENTRIES: list[dict] = [
    {
        "q": ["what is tei-ha", "who are you", "about company", "about tei-ha"],
        "a": (
            f"{COMPANY_PROFILE['name']} — {COMPANY_PROFILE['tagline']}. "
            f"We are based in {COMPANY_PROFILE['location']} and deliver end-to-end building solutions: "
            f"{', '.join(COMPANY_PROFILE['services'])}."
        ),
    },
    {
        "q": ["contact", "email", "reach you", "support"],
        "a": f"You can reach us at {COMPANY_PROFILE['email']}. We’ll be happy to help.",
    },
    {
        "q": ["where are you", "location", "address"],
        "a": f"Our location: {COMPANY_PROFILE['location']}.",
    },
    {
        "q": ["services", "what do you offer", "offerings"],
        "a": "Our core services include: " + ", ".join(COMPANY_PROFILE["services"]) + ".",
    },
    {
        "q": ["ai tools", "tools", "budget sensei", "style fusion", "site scout", "sketch"],
        "a": (
            "Available AI tools: "
            + ", ".join(COMPANY_PROFILE["ai_tools"])
            + ". Visit the AI Tools page to try them out."
        ),
    },
    {
        "q": ["pricing", "plans", "subscription", "cost"],
        "a": (
            "Plans: Free (limited), Pro (higher limits), Max (highest limits). "
            f"Local demo pricing: Pro ~ {COMPANY_PROFILE['plans']['pro'].split('typically ')[-1].rstrip('.')}, "
            f"Max ~ {COMPANY_PROFILE['plans']['max'].split('typically ')[-1].rstrip('.')}. "
            "See the Pricing page for currency/cycle options."
        ),
    },
    {
        "q": ["payment", "pay", "mobile money", "mtn", "airtel", "card"],
        "a": "Payment methods: MTN Mobile Money, Airtel Money, and Cards (coming soon).",
    },
    {
        "q": ["youtube", "social", "channel"],
        "a": f"YouTube: {COMPANY_PROFILE['social']['youtube']}",
    },
]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _answer_from_kb(user_message: str) -> Optional[str]:
    """
    Lightweight matcher: score by fuzzy match against triggers,
    and also keyword coverage to reduce false positives.
    """
    if not user_message or not user_message.strip():
        return None
    msg = user_message.strip().lower()
    best_score = 0.0
    best_answer: Optional[str] = None

    for entry in FAQ_ENTRIES:
        triggers = entry.get("q", [])
        # Max fuzzy score across triggers
        fuzzy = max((_similarity(msg, t) for t in triggers), default=0.0)
        # Simple keyword overlap score
        tokens = set(msg.split())
        key_tokens = set()
        for t in triggers:
            key_tokens.update(t.split())
        overlap = len(tokens & key_tokens) / max(1, len(key_tokens))
        score = 0.7 * fuzzy + 0.3 * overlap
        if score > best_score:
            best_score = score
            best_answer = entry.get("a")

    # Also handle very generic questions by extracting key intents
    if best_score < 0.45:
        if any(k in msg for k in ["contact", "email", "reach"]):
            return f"Contact us at {COMPANY_PROFILE['email']}."
        if any(k in msg for k in ["service", "offer"]):
            return "We offer: " + ", ".join(COMPANY_PROFILE["services"]) + "."
        if any(k in msg for k in ["price", "plan", "subscription", "cost"]):
            return (
                "Plans: Free (limited), Pro, Max. See the Pricing page for details; "
                "local demo pricing shows Pro and Max monthly options in UGX."
            )
        if any(k in msg for k in ["tool", "ai", "budget", "sketch", "style", "site"]):
            return "Our AI tools include Budget Sensei, Inspiration Sketch Pad, Style Fusion, and Virtual Site Scout."
        if any(k in msg for k in ["where", "location", "address"]):
            return f"We are located in {COMPANY_PROFILE['location']}."

    # Threshold to return a confident answer
    if best_score >= 0.45 and best_answer:
        return best_answer
    return None

class MobileMoneyPayment(BaseModel):
    phone_number: str      # Format: 256700123456
    amount: float
    plan: str              # pro, max
    email: str
    network: str = "mtn"   # mtn or airtel


def _send_email(to_email: str, subject: str, body: str):
    if not SMTP_HOST or not SMTP_FROM:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def notify_admin(background: BackgroundTasks, subject: str, body: str):
    if ADMIN_EMAIL:
        background.add_task(_send_email, ADMIN_EMAIL, subject, body)


def send_welcome(background: BackgroundTasks, user_email: str):
    subject = "Welcome to TEI-HA AI Tools"
    body = (
        "Thank you for trying TEI-HA Construction Services AI tools.\n\n"
        "Disclaimer: The AI outputs are indicative and not a final say. "
        "Please contact TEI-HA Construction Services Ltd to draw final professional conclusions.\n\n"
        "We appreciate your interest!"
    )
    background.add_task(_send_email, user_email, subject, body)


def get_user(email: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT email, prompts_used, chars_used, welcome_sent, window_started_at FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "email": row[0],
            "prompts_used": row[1],
            "chars_used": row[2],
            "welcome_sent": row[3],
            "window_started_at": row[4],
        }
    finally:
        conn.close()


def create_user(email: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (email, created_at, prompts_used, chars_used, welcome_sent, window_started_at) VALUES (?, ?, 0, 0, 0, ?)",
            (email, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def update_user_usage(email: str, add_prompts: int, add_chars: int):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET prompts_used = prompts_used + ?, chars_used = chars_used + ? WHERE email = ?",
            (add_prompts, add_chars, email),
        )
        conn.commit()
    finally:
        conn.close()


def set_welcome_sent(email: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET welcome_sent = 1 WHERE email = ?", (email,))
        conn.commit()
    finally:
        conn.close()


FREE_PROMPT_LIMIT = 5
FREE_CHAR_LIMIT = 5000

PRO_PROMPT_LIMIT = 200
PRO_CHAR_LIMIT = 500_000
MAX_PROMPT_LIMIT = 1000
MAX_CHAR_LIMIT = 5_000_000

PLAN_LIMITS = {
    "free": {"prompts": FREE_PROMPT_LIMIT, "chars": FREE_CHAR_LIMIT},
    "pro": {"prompts": PRO_PROMPT_LIMIT, "chars": PRO_CHAR_LIMIT},
    "max": {"prompts": MAX_PROMPT_LIMIT, "chars": MAX_CHAR_LIMIT},
}

def get_active_subscription(email: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT tier, cycle, currency, status, current_period_end, provider FROM subscriptions WHERE email = ?",
            (email,),
        )
        row = cur.fetchone()
        if not row:
            return None
        sub = {
            "tier": row[0],
            "cycle": row[1],
            "currency": row[2],
            "status": row[3],
            "current_period_end": row[4],
            "provider": row[5],
        }
        # Check active
        try:
            end_dt = datetime.fromisoformat(sub["current_period_end"])
        except Exception:
            end_dt = datetime.utcnow()
        if sub["status"] != "active" or end_dt < datetime.utcnow():
            return None
        return sub
    finally:
        conn.close()


def enforce_quota(email: str, incoming_chars: int):
    user = get_user(email)
    if not user:
        create_user(email)
        user = get_user(email)

    # Reset usage if 24h window elapsed
    try:
        window_started_at = user.get("window_started_at")
        window_dt = datetime.fromisoformat(window_started_at) if window_started_at else None
    except Exception:
        window_dt = None
    now_dt = datetime.utcnow()
    if not window_dt or (now_dt - window_dt).total_seconds() >= 24 * 3600:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET prompts_used = 0, chars_used = 0, window_started_at = ? WHERE email = ?",
                (now_dt.isoformat(), email),
            )
            conn.commit()
        finally:
            conn.close()
        user = get_user(email)

    prompts_used = int(user["prompts_used"])
    chars_used = int(user["chars_used"])

    # Compute remaining time to reset for helpful message
    retry_after_seconds = 0
    try:
        window_started_at = user.get("window_started_at")
        window_dt = datetime.fromisoformat(window_started_at) if window_started_at else now_dt
        elapsed = (now_dt - window_dt).total_seconds()
        retry_after_seconds = max(0, int(24 * 3600 - elapsed))
    except Exception:
        retry_after_seconds = 24 * 3600

    # Determine plan limits
    sub = get_active_subscription(email)
    plan_key = (sub["tier"] if sub else "free").lower()
    limits = PLAN_LIMITS.get(plan_key, PLAN_LIMITS["free"])

    if prompts_used >= limits["prompts"] or (chars_used + max(0, incoming_chars) > limits["chars"]):
        message = "You have reached your maximum free points usage, try again after 24 hours."
        try:
            reset_at = (window_dt + timedelta(seconds=24 * 3600)).isoformat()
        except Exception:
            reset_at = None
        raise HTTPException(
            status_code=429,
            detail={
                "error": "limit_reached",
                "message": message if plan_key == "free" else "You have reached your current plan limit. Please upgrade or wait for reset.",
                "prompts_used": prompts_used,
                "limit_prompts": limits["prompts"],
                "chars_used": chars_used,
                "limit_chars": limits["chars"],
                "retry_after_seconds": retry_after_seconds,
                "reset_at": reset_at,
                "plan": plan_key,
            },
        )

def save_session(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO sessions (id, created_at) VALUES (?, ?)", (session_id, datetime.utcnow().isoformat()))
        conn.commit()
    finally:
        conn.close()


def save_message(session_id: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, role, content, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}


class RegisterRequest(BaseModel):
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None


@app.post("/api/users/register")
def register_user(body: RegisterRequest, background: BackgroundTasks):
    email = (body.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    create_user(email)
    user = get_user(email)
    if user and not user["welcome_sent"]:
        send_welcome(background, email)
        set_welcome_sent(email)
    # Include name and phone in admin notification if provided
    name = (body.name or "").strip()
    phone = (body.phone or "").strip()
    admin_msg = f"User registered: {email}"
    if name:
        admin_msg += f" (Name: {name})"
    if phone:
        admin_msg += f" (Phone: {phone})"
    admin_msg += f" at {datetime.utcnow().isoformat()}"
    notify_admin(background, "New AI tools signup", admin_msg)
    return {"status": "ok"}


# -------- OAuth Endpoints --------
@app.get("/api/auth/google/login")
async def google_login():
    """Initiate Google OAuth login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
    
    redirect_uri = f"{FRONTEND_URL}/ai-tools.html"
    google_oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid email profile&"
        "access_type=offline"
    )
    return {"auth_url": google_oauth_url}


@app.get("/api/auth/microsoft/login")
async def microsoft_login():
    """Initiate Microsoft/Outlook OAuth login"""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Microsoft OAuth is not configured. Please set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET environment variables.")
    
    redirect_uri = f"{FRONTEND_URL}/ai-tools.html"
    microsoft_oauth_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={MICROSOFT_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid email profile&"
        "response_mode=query"
    )
    return {"auth_url": microsoft_oauth_url}


@app.get("/api/auth/google/callback")
async def google_callback(code: str, background: BackgroundTasks):
    """Handle Google OAuth callback"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    
    try:
        redirect_uri = f"{FRONTEND_URL}/ai-tools.html"
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()
            
            if "access_token" not in token_data:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            user_data = user_response.json()
            
            email = (user_data.get("email") or "").strip().lower()
            name = user_data.get("name", "").strip()
            
            if not email or "@" not in email:
                raise HTTPException(status_code=400, detail="Invalid user data from Google")
            
            # Create or update user
            create_user(email)
            user = get_user(email)
            if user and not user["welcome_sent"]:
                send_welcome(background, email)
                set_welcome_sent(email)
            
            notify_admin(background, "New OAuth signup", f"User signed in via Google: {email} (Name: {name}) at {datetime.utcnow().isoformat()}")
            
            return {
                "status": "ok",
                "email": email,
                "name": name,
                "provider": "google"
            }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.get("/api/auth/microsoft/callback")
async def microsoft_callback(code: str, background: BackgroundTasks):
    """Handle Microsoft/Outlook OAuth callback"""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Microsoft OAuth is not configured")
    
    try:
        redirect_uri = f"{FRONTEND_URL}/ai-tools.html"
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "code": code,
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": "openid email profile",
                },
            )
            token_data = token_response.json()
            
            if "access_token" not in token_data:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            # Get user info
            user_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            user_data = user_response.json()
            
            email = (user_data.get("mail") or user_data.get("userPrincipalName") or "").strip().lower()
            name = user_data.get("displayName", "").strip()
            
            if not email or "@" not in email:
                raise HTTPException(status_code=400, detail="Invalid user data from Microsoft")
            
            # Create or update user
            create_user(email)
            user = get_user(email)
            if user and not user["welcome_sent"]:
                send_welcome(background, email)
                set_welcome_sent(email)
            
            notify_admin(background, "New OAuth signup", f"User signed in via Microsoft: {email} (Name: {name}) at {datetime.utcnow().isoformat()}")
            
            return {
                "status": "ok",
                "email": email,
                "name": name,
                "provider": "microsoft"
            }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    session_id = body.session_id or str(uuid.uuid4())
    save_session(session_id)
    save_message(session_id, "user", message)

    # Prefer n8n webhook if set, else fallback
    reply_text: str
    # 1) Try to answer from local company knowledge base
    kb_answer = _answer_from_kb(message)
    if kb_answer:
        reply_text = kb_answer
    elif N8N_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    N8N_WEBHOOK_URL,
                    json={"session_id": session_id, "message": message},
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                # Try to parse structured response first, else use raw text
                data = None
                try:
                    data = resp.json()
                except Exception:
                    pass
                if isinstance(data, dict) and "reply" in data:
                    reply_text = str(data["reply"])
                elif isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and "reply" in data["data"]:
                    reply_text = str(data["data"]["reply"])
                else:
                    reply_text = resp.text.strip() or "I'm here to help. Could you please clarify your question?"
        except Exception as e:
            # Fallback on error contacting n8n
            reply_text = (
                "I’m here to help with TEI-HA questions. "
                "For direct assistance, contact teihaconstructionservices@gmail.com."
            )
    else:
        # Simple placeholder response; replace with model integration as needed
        reply_text = (
            "I’m the TEI-HA assistant. You can ask about our services, pricing, AI tools, location, or contact. "
            f"Email: {COMPANY_PROFILE['email']}."
        )

    save_message(session_id, "assistant", reply_text)
    return ChatResponse(reply=reply_text, session_id=session_id)


# -------- AI Tools Endpoints --------
class BudgetRequest(BaseModel):
    email: str
    project_type: str
    built_up_area_sqm: float
    num_storeys: int = 1
    finish_level: str = "standard"  # basic | standard | premium
    location: str = "Kampala"


@app.post("/api/tools/budget")
async def budget_tool(req: BudgetRequest, background: BackgroundTasks):
    email = (req.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    incoming_chars = len(f"{req.project_type} {req.location}") + 20
    enforce_quota(email, incoming_chars)
    # Very simple heuristic baseline costs (UGX per sqm)
    base_map = {
        "residential": 1_500_000,
        "commercial": 1_800_000,
        "industrial": 2_000_000,
        "infrastructure": 2_200_000,
    }
    finish_factor = {"basic": 0.9, "standard": 1.0, "premium": 1.25}
    location_factor = 1.0 + (0.08 if req.location.lower() in {"kampala", "wakiso"} else 0.0)

    base_cost = base_map.get(req.project_type.lower(), 1_600_000)
    finish_mult = finish_factor.get(req.finish_level.lower(), 1.0)

    structure_complexity = 1.0 + max(0, req.num_storeys - 1) * 0.05

    cost_per_sqm = base_cost * finish_mult * location_factor * structure_complexity
    subtotal = cost_per_sqm * max(0.0, req.built_up_area_sqm)

    # Soft costs and contingency
    professional_fees = 0.08 * subtotal
    contingency = 0.10 * subtotal
    taxes = 0.18 * (subtotal + professional_fees)  # sample VAT on works + prof fees
    grand_total = subtotal + professional_fees + contingency + taxes

    result = {
        "inputs": req.dict(),
        "breakdown": {
            "cost_per_sqm": int(cost_per_sqm),
            "construction_subtotal": int(subtotal),
            "professional_fees": int(professional_fees),
            "contingency": int(contingency),
            "taxes": int(taxes),
        },
        "grand_total": int(grand_total),
        "currency": "UGX",
        "note": "Estimates are indicative and should be refined with detailed BOQs and site assessments.",
    }
    update_user_usage(email, 1, incoming_chars)
    notify_admin(background, "AI Tool Used - Budget", f"User {email} requested budget estimate at {datetime.utcnow().isoformat()}")
    return result


@app.post("/api/tools/sketch")
async def sketch_tool(
    background: BackgroundTasks,
    email: str = Form(...),
    prompt: str = Form(""),
    image: UploadFile = File(None),
):
    email = (email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    incoming_chars = len(prompt or "")
    enforce_quota(email, incoming_chars)
    # Save image if provided
    saved_path = None
    if image is not None:
        uploads_dir = os.path.join(os.path.dirname(DB_PATH), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}_{image.filename}"
        saved_path = os.path.join(uploads_dir, filename)
        with open(saved_path, "wb") as f:
            f.write(await image.read())

    # If n8n is configured, forward
    if N8N_WEBHOOK_URL:
        payload = {"tool": "sketch", "prompt": prompt, "image_path": saved_path}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(N8N_WEBHOOK_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {"status": "ok", "result": data}
        except Exception as e:
            return {"status": "degraded", "message": "n8n unavailable, returning placeholder result", "prompt": prompt, "image_saved": bool(saved_path)}

    # Placeholder response
    update_user_usage(email, 1, incoming_chars)
    notify_admin(background, "AI Tool Used - Sketch", f"User {email} submitted sketch at {datetime.utcnow().isoformat()}")
    return {
        "status": "ok",
        "message": "Sketch received. AI render pipeline will process this in production.",
        "prompt": prompt,
        "image_saved": bool(saved_path),
    }


class StyleFusionRequest(BaseModel):
    email: str
    styles: list[str] = []
    color_palette: list[str] = []
    rooms: list[str] = []


@app.post("/api/tools/style-fusion")
async def style_fusion_tool(req: StyleFusionRequest, background: BackgroundTasks):
    email = (req.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    incoming_chars = len(" ".join(req.styles + req.color_palette + req.rooms))
    enforce_quota(email, incoming_chars)
    if N8N_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(N8N_WEBHOOK_URL, json={"tool": "style-fusion", **req.dict()})
                resp.raise_for_status()
                return {"status": "ok", "result": resp.json()}
        except Exception:
            pass

    # Placeholder: generate simple mood-board suggestions
    suggestions = [
        f"Combine {', '.join(req.styles) or 'modern'} elements with a palette of {', '.join(req.color_palette) or 'neutrals'}",
        f"Use natural textures (wood, stone) to add warmth to {', '.join(req.rooms) or 'living spaces'}",
        "Emphasize lighting layers: ambient, task, and accent to shape mood",
    ]
    update_user_usage(email, 1, incoming_chars)
    notify_admin(background, "AI Tool Used - Style Fusion", f"User {email} requested style fusion at {datetime.utcnow().isoformat()}")
    return {"status": "ok", "suggestions": suggestions}


class SiteScoutRequest(BaseModel):
    email: str
    address: str
    plot_size_sqm: float | None = None


@app.post("/api/tools/site-scout")
async def site_scout_tool(req: SiteScoutRequest, background: BackgroundTasks):
    email = (req.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    incoming_chars = len(req.address or "") + (0 if req.plot_size_sqm is None else 6)
    enforce_quota(email, incoming_chars)
    # If n8n exists, delegate for enrichment (geocoding, regs, etc.)
    if N8N_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(N8N_WEBHOOK_URL, json={"tool": "site-scout", **req.dict()})
                resp.raise_for_status()
                return {"status": "ok", "result": resp.json()}
        except Exception:
            pass

    # Placeholder assessment
    assessment = [
        f"Location: {req.address}",
        "Access and logistics: verify road width, turning radius for deliveries, and staging area.",
        "Topography: confirm contour survey; allow for drainage and retaining where needed.",
        "Soils: conduct geotechnical tests; consider bearing capacity and groundwater depth.",
        "Utilities: validate proximity to power, water, and sewer; plan for connection fees.",
        "Regulatory: check zoning, plot coverage, height limits, and setbacks with local authority.",
    ]
    update_user_usage(email, 1, incoming_chars)
    notify_admin(background, "AI Tool Used - Site Scout", f"User {email} requested site assessment at {datetime.utcnow().isoformat()}")
    return {"status": "ok", "assessment": assessment, "plot_size_sqm": req.plot_size_sqm}


# -------- Billing (Scaffold) --------
class CheckoutRequest(BaseModel):
    email: str
    provider: str  # stripe | flutterwave
    price_key: str  # e.g., pro_month_USD
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class SubscriptionResponse(BaseModel):
    tier: str
    cycle: str
    currency: str
    status: str
    current_period_end: Optional[str] = None

# Example price catalog mapping for scaffold
PRICE_CATALOG = {
    # USD
    "free_week_USD": ("free", "week", "USD"),
    "free_month_USD": ("free", "month", "USD"),
    "free_year_USD": ("free", "year", "USD"),
    "pro_week_USD": ("pro", "week", "USD"),
    "pro_month_USD": ("pro", "month", "USD"),
    "pro_year_USD": ("pro", "year", "USD"),
    "max_week_USD": ("max", "week", "USD"),
    "max_month_USD": ("max", "month", "USD"),
    "max_year_USD": ("max", "year", "USD"),
    # UGX
    "free_week_UGX": ("free", "week", "UGX"),
    "free_month_UGX": ("free", "month", "UGX"),
    "free_year_UGX": ("free", "year", "UGX"),
    "pro_week_UGX": ("pro", "week", "UGX"),
    "pro_month_UGX": ("pro", "month", "UGX"),
    "pro_year_UGX": ("pro", "year", "UGX"),
    "max_week_UGX": ("max", "week", "UGX"),
    "max_month_UGX": ("max", "month", "UGX"),
    "max_year_UGX": ("max", "year", "UGX"),
}

def _cycle_to_delta(cycle: str) -> timedelta:
    if cycle == "week":
        return timedelta(days=7)
    if cycle == "month":
        return timedelta(days=30)
    if cycle == "year":
        return timedelta(days=365)
    return timedelta(days=30)

def upsert_subscription(email: str, tier: str, cycle: str, currency: str, provider: str, period_end: datetime | None = None, status: str = "active"):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        end_iso = (period_end or (datetime.utcnow() + _cycle_to_delta(cycle))).isoformat()
        cur.execute(
            """
            INSERT INTO subscriptions (email, tier, cycle, currency, status, current_period_end, provider, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                tier=excluded.tier,
                cycle=excluded.cycle,
                currency=excluded.currency,
                status=excluded.status,
                current_period_end=excluded.current_period_end,
                provider=excluded.provider,
                updated_at=excluded.updated_at
            """,
            (email, tier, cycle, currency, status, end_iso, provider, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

@app.get("/api/billing/subscription", response_model=SubscriptionResponse)
def get_subscription(email: str):
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        # default free
        return SubscriptionResponse(tier="free", cycle="month", currency="USD", status="active", current_period_end=None)
    sub = get_active_subscription(email)
    if not sub:
        return SubscriptionResponse(tier="free", cycle="month", currency="USD", status="active", current_period_end=None)
    return SubscriptionResponse(**sub)

@app.post("/api/billing/checkout")
def create_checkout(req: CheckoutRequest):
    email = (req.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if req.price_key not in PRICE_CATALOG:
        raise HTTPException(status_code=400, detail="Unknown price_key")
    # Scaffold: return a mock checkout URL that the frontend can "simulate"
    success = req.success_url or "http://localhost:5500/pricing.html"
    cancel = req.cancel_url or "http://localhost:5500/pricing.html"
    checkout_url = f"{success}?mock_checkout=1&provider={req.provider}&price_key={req.price_key}&email={email}"
    return {"checkout_url": checkout_url}

@app.post("/api/billing/mock/activate")
def mock_activate(price_key: str, email: str, provider: str = "stripe"):
    email = (email or "").strip().lower()
    if price_key not in PRICE_CATALOG:
        raise HTTPException(status_code=400, detail="Unknown price_key")
    tier, cycle, currency = PRICE_CATALOG[price_key]
    upsert_subscription(email, tier, cycle, currency, provider)
    return {"status": "ok", "tier": tier, "cycle": cycle, "currency": currency}

@app.post("/api/billing/webhook/stripe")
def stripe_webhook(payload: dict):
    # Scaffold placeholder: verify and update subscription here
    # In production: verify signature header, decode event, extract customer/subscription
    return {"status": "received"}

@app.post("/api/billing/webhook/flutterwave")
def flutterwave_webhook(payload: dict):
    # Scaffold placeholder for Flutterwave webhook handler
    return {"status": "received"}


# -------- Users (Profile) --------
@app.get("/api/users/me")
def users_me(email: str):
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    user = get_user(email)
    if not user:
        create_user(email)
        user = get_user(email)
    # compute reset time
    try:
        window_dt = datetime.fromisoformat(user.get("window_started_at") or datetime.utcnow().isoformat())
    except Exception:
        window_dt = datetime.utcnow()
    reset_at = (window_dt + timedelta(seconds=24 * 3600)).isoformat()
    sub = get_active_subscription(email)
    plan_key = (sub["tier"] if sub else "free").lower()
    limits = PLAN_LIMITS.get(plan_key, PLAN_LIMITS["free"])
    return {
        "email": email,
        "usage": {
            "prompts_used": int(user["prompts_used"]),
            "chars_used": int(user["chars_used"]),
            "reset_at": reset_at,
        },
        "subscription": {
            "tier": plan_key,
            "cycle": (sub["cycle"] if sub else "month"),
            "currency": (sub["currency"] if sub else "USD"),
            "status": ("active" if sub else "active"),
            "current_period_end": (sub["current_period_end"] if sub else None),
        },
        "limits": {
            "prompt_limit": limits["prompts"],
            "char_limit": limits["chars"],
        },
    }

# ====== AFRICA'S TALKING MOBILE MONEY PAYMENTS ======

@app.post("/api/payments/mobile-money/request")
async def request_mobile_money_payment(payment: MobileMoneyPayment):
    """Request mobile money payment via Africa's Talking"""
    try:
        # Plan pricing in UGX
        plan_prices = {
            "pro": 35000,   # 35,000 UGX
            "max": 95000    # 95,000 UGX
        }
        
        amount = plan_prices.get(payment.plan, 35000)
        
        # Validate phone number format
        if not payment.phone_number.startswith("256") or len(payment.phone_number) != 12:
            raise HTTPException(
                status_code=400, 
                detail="Invalid phone number. Use format: 256700123456"
            )
        
        # Check if Africa's Talking is initialized
        if not at_payments:
            # Test mode response
            return {
                "status": "pending",
                "message": f"TEST MODE: Payment request for {amount} UGX",
                "transaction_id": f"test_{int(datetime.utcnow().timestamp())}",
                "amount": amount,
                "currency": "UGX",
                "phone": payment.phone_number,
                "network": payment.network,
                "plan": payment.plan,
                "test_mode": True
            }
        
        # Real Africa's Talking request
        product_name = "TEI-HA AI Tools"
        metadata = {
            "plan": payment.plan,
            "email": payment.email,
            "network": payment.network,
            "description": f"{payment.plan.upper()} Plan Subscription"
        }
        
        print(f"🌍 Sending mobile money request: {amount} UGX to {payment.phone_number}")
        
        response = at_payments.mobile_checkout(
            product_name=product_name,
            phone_number=payment.phone_number,
            currency_code="UGX",
            amount=amount,
            metadata=metadata
        )
        
        print(f"🌍 Africa's Talking response: {response}")
        
        if response.get("status") in ["PendingConfirmation", "Success"]:
            return {
                "status": "pending",
                "message": f"📱 Check your {payment.network.upper()} phone! Approve the payment.",
                "transaction_id": response.get("transactionId", ""),
                "amount": amount,
                "currency": "UGX",
                "phone": payment.phone_number,
                "network": payment.network,
                "plan": payment.plan,
                "test_mode": False
            }
        else:
            error_msg = response.get("description", "Payment request failed")
            raise HTTPException(status_code=400, detail=error_msg)
            
    except Exception as e:
        print(f"❌ Mobile money error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@app.post("/api/payments/mobile-money/complete")
async def complete_mobile_money_payment(transaction_id: str, email: str, plan: str = "pro"):
    """Complete payment and activate subscription"""
    try:
        # Update user subscription
        upsert_subscription(
            email=email,
            tier=plan,
            cycle="month",
            currency="UGX",
            provider="mobile_money"
        )
        
        # Send confirmation email
        try:
            subject = "🎉 TEI-HA Subscription Activated!"
            body = f"""
            Hello,
            
            Your {plan.upper()} plan subscription has been activated!
            
            You now have access to:
            - Higher usage limits
            - Priority AI tools
            - Enhanced features
            
            Thank you for choosing TEI-HA Construction Services!
            
            Best regards,
            TEI-HA Team
            """
            
            _send_email(email, subject, body)
        except Exception as email_error:
            print(f"Email send failed (but subscription saved): {email_error}")
        
        return {
            "status": "success",
            "message": "✅ Payment confirmed! Subscription activated.",
            "tier": plan,
            "email": email,
            "currency": "UGX"
        }
        
    except Exception as e:
        print(f"❌ Error completing payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error completing payment: {str(e)}")