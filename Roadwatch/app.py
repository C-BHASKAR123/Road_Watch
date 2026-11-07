"""RoadWatch — a small Flask application for reporting road problems.

The app intentionally uses Python's built-in SQLite driver so it can run with a
single third-party dependency (Flask). Run ``python app.py`` for local use.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import ssl
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlparse
from urllib.request import Request as UrlRequest, urlopen

import click
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
DEFAULT_DATABASE = INSTANCE_DIR / "roadwatch.db"

STATUSES = ("Submitted", "Under Review", "In Progress", "Resolved", "Rejected")
PUBLIC_STATUSES = ("Submitted", "Under Review", "In Progress", "Resolved")
ISSUE_TYPES = (
    "Pothole",
    "Damaged road surface",
    "Waterlogging",
    "Broken footpath",
    "Missing or damaged signage",
    "Streetlight problem",
    "Other",
)
SEVERITIES = ("Low", "Medium", "High", "Critical")
SEVERITY_HELP = {
    "Low": "A nuisance, but traffic can pass safely.",
    "Medium": "Needs attention; could worsen over time.",
    "High": "A serious hazard for vehicles or pedestrians.",
    "Critical": "An immediate danger to public safety.",
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TRACKING_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_PHOTO_BYTES = 8 * 1024 * 1024
PUBLIC_PAGE_SIZE = 6
ADMIN_PAGE_SIZE = 10
PASSWORD_MIN_LENGTH = 12
PASSWORD_RESET_TTL_MINUTES = 30
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPES = "openid email profile"


def _env_list(name: str) -> list[str]:
    return [
        value.strip().lower()
        for value in (os.environ.get(name) or "").split(",")
        if value.strip()
    ]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, ""))
    except ValueError:
        return default


SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    email TEXT,
    google_sub TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_number TEXT NOT NULL UNIQUE,
    reporter_name TEXT NOT NULL,
    reporter_email TEXT,
    reporter_phone TEXT,
    road_name TEXT NOT NULL,
    location TEXT NOT NULL,
    city TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    photo_filename TEXT,
    status TEXT NOT NULL DEFAULT 'Submitted',
    admin_note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports (created_at DESC);

CREATE TABLE IF NOT EXISTS report_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    note TEXT,
    admin_username TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_report_updates_report_id
    ON report_updates (report_id, created_at);

CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES admins (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_password_resets_admin
    ON password_resets (admin_id, created_at DESC);
"""

# Indexes that reference columns added by the migration below. They are created
# after the migration so older databases keep working.
AUTH_INDEXES = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_admins_email
    ON admins (email COLLATE NOCASE)
    WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_admins_google_sub
    ON admins (google_sub)
    WHERE google_sub IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_password_resets_token
    ON password_resets (token_hash);
"""


def _load_or_create_secret_key() -> str:
    """Use SECRET_KEY when provided, otherwise keep a stable local key."""
    configured = os.environ.get("SECRET_KEY")
    if configured:
        return configured

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    key_path = INSTANCE_DIR / ".secret_key"
    if key_path.exists():
        stored = key_path.read_text(encoding="utf-8").strip()
        if stored:
            return stored

    key = secrets.token_hex(32)
    key_path.write_text(key, encoding="utf-8")
    return key


def _database_path() -> str:
    configured = os.environ.get("ROADWATCH_DATABASE")
    path = Path(configured).expanduser() if configured else DEFAULT_DATABASE
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path)


app = Flask(__name__, instance_path=str(INSTANCE_DIR))
app.config.from_mapping(
    SECRET_KEY=_load_or_create_secret_key(),
    DATABASE=_database_path(),
    MAX_CONTENT_LENGTH=MAX_PHOTO_BYTES + (512 * 1024),
    UPLOAD_FOLDER=str(UPLOAD_DIR),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("ROADWATCH_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    PASSWORD_RESET_TTL_MINUTES=_env_int(
        "ROADWATCH_RESET_TTL_MINUTES", PASSWORD_RESET_TTL_MINUTES
    ),
    SHOW_RESET_LINK=os.environ.get("ROADWATCH_SHOW_RESET_LINK") == "1",
    GOOGLE_CLIENT_ID=(os.environ.get("GOOGLE_CLIENT_ID") or "").strip(),
    GOOGLE_CLIENT_SECRET=(os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip(),
    GOOGLE_REDIRECT_URI=(os.environ.get("GOOGLE_REDIRECT_URI") or "").strip(),
    GOOGLE_ALLOWED_EMAILS=_env_list("ROADWATCH_GOOGLE_ALLOWED_EMAILS"),
    SMTP_HOST=(os.environ.get("ROADWATCH_SMTP_HOST") or "").strip(),
    SMTP_PORT=_env_int("ROADWATCH_SMTP_PORT", 587),
    SMTP_USERNAME=(os.environ.get("ROADWATCH_SMTP_USERNAME") or "").strip(),
    SMTP_PASSWORD=os.environ.get("ROADWATCH_SMTP_PASSWORD") or "",
    SMTP_FROM=(os.environ.get("ROADWATCH_SMTP_FROM") or "").strip(),
    SMTP_USE_SSL=os.environ.get("ROADWATCH_SMTP_SSL") == "1",
    SMTP_STARTTLS=os.environ.get("ROADWATCH_SMTP_STARTTLS", "1") != "0",
)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exception: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_column(
    db: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    db = get_db()
    db.executescript(SCHEMA)
    _ensure_column(db, "admins", "email", "TEXT")
    _ensure_column(db, "admins", "google_sub", "TEXT")
    db.executescript(AUTH_INDEXES)
    db.commit()


def seed_default_admin() -> None:
    """Create a local admin only when no admin account exists yet."""
    db = get_db()
    existing = db.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
    if existing:
        return

    username = (os.environ.get("ROADWATCH_ADMIN_USERNAME") or "admin").strip()
    password = os.environ.get("ROADWATCH_ADMIN_PASSWORD") or "roadwatch123"
    db.execute(
        "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), utc_now_string()),
    )
    db.commit()
    current_app.logger.warning(
        "Created the first admin account '%s'. If ROADWATCH_ADMIN_PASSWORD was "
        "not set, it uses the development password 'roadwatch123'. Change it with "
        "'flask --app app create-admin' before deploying.",
        username,
    )


def initialize_app() -> None:
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        init_db()
        seed_default_admin()


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_string() -> str:
    return utc_now().strftime("%Y-%m-%d %H:%M:%S")


def is_safe_next_url(target: str | None) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    return (
        not parsed.scheme
        and not parsed.netloc
        and target.startswith("/")
        and not target.startswith("//")
    )


def get_csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def login_required(view):
    # Admin sign-in has been removed; administrative pages are open.
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        return view(*args, **kwargs)

    return wrapped_view


PASSWORD_RULES = (
    (
        f"At least {PASSWORD_MIN_LENGTH} characters",
        lambda value: len(value) >= PASSWORD_MIN_LENGTH,
    ),
    ("An uppercase letter (A-Z)", lambda value: bool(re.search(r"[A-Z]", value))),
    ("A lowercase letter (a-z)", lambda value: bool(re.search(r"[a-z]", value))),
    ("A number (0-9)", lambda value: bool(re.search(r"[0-9]", value))),
    (
        "A symbol such as ! ? @ # $ %",
        lambda value: bool(re.search(r"[^A-Za-z0-9]", value)),
    ),
)

COMMON_PASSWORDS = {
    "admin123",
    "letmein123",
    "password",
    "password123",
    "qwerty123",
    "roadwatch",
    "roadwatch123",
    "welcome123",
}


def password_problems(
    password: str, username: str = "", email: str = ""
) -> list[str]:
    """Return human-readable reasons why a password is not strong enough."""
    problems = [label for label, rule in PASSWORD_RULES if not rule(password)]
    lowered = password.lower()

    if lowered in COMMON_PASSWORDS:
        problems.append("Is not a commonly used password")
    if username and len(username) >= 3 and username.lower() in lowered:
        problems.append("Does not contain your username")
    if email:
        local_part = email.split("@")[0].lower()
        if len(local_part) >= 3 and local_part in lowered:
            problems.append("Does not contain your email name")
    if "roadwatch" in lowered:
        problems.append("Does not contain the site name")

    # Keep the order stable while removing duplicates.
    return list(dict.fromkeys(problems))


def get_admin(admin_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT * FROM admins WHERE id = ?", (admin_id,)
    ).fetchone()


def sign_in_admin(admin: sqlite3.Row) -> None:
    session.clear()
    session["admin_id"] = admin["id"]
    session["admin_username"] = admin["username"]
    session.permanent = True


def smtp_configured() -> bool:
    config = current_app.config
    return bool(config["SMTP_HOST"] and (config["SMTP_FROM"] or config["SMTP_USERNAME"]))


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    """Send a reset link when SMTP is configured. Never raise to the caller."""
    config = current_app.config
    host = config["SMTP_HOST"]
    sender = config["SMTP_FROM"] or config["SMTP_USERNAME"]
    if not host or not sender or not to_email:
        return False

    message = EmailMessage()
    message["Subject"] = "Reset your RoadWatch password"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
        "Someone requested a password reset for your RoadWatch admin account.\n\n"
        f"Open this link within {config['PASSWORD_RESET_TTL_MINUTES']} minutes:\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can ignore this email. Your password "
        "will not change until the link is used."
    )

    try:
        context = ssl.create_default_context()
        if config["SMTP_USE_SSL"]:
            server = smtplib.SMTP_SSL(
                host, config["SMTP_PORT"], timeout=15, context=context
            )
        else:
            server = smtplib.SMTP(host, config["SMTP_PORT"], timeout=15)
            server.ehlo()
            if config["SMTP_STARTTLS"]:
                server.starttls(context=context)
                server.ehlo()
        try:
            if config["SMTP_USERNAME"]:
                server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            server.send_message(message)
        finally:
            server.quit()
        return True
    except (OSError, smtplib.SMTPException) as exc:
        current_app.logger.warning("Could not send password reset email: %s", exc)
        return False


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset(db: sqlite3.Connection, admin_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = utc_now()
    expires = now + timedelta(
        minutes=current_app.config["PASSWORD_RESET_TTL_MINUTES"]
    )
    db.execute(
        "DELETE FROM password_resets WHERE admin_id = ? AND used_at IS NULL",
        (admin_id,),
    )
    db.execute(
        """
        INSERT INTO password_resets
        (admin_id, token_hash, expires_at, used_at, created_at)
        VALUES (?, ?, ?, NULL, ?)
        """,
        (
            admin_id,
            hash_reset_token(token),
            expires.strftime("%Y-%m-%d %H:%M:%S"),
            now.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    db.commit()
    return token


def find_password_reset(db: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    if not token or len(token) > 200:
        return None
    return db.execute(
        """
        SELECT pr.id AS reset_id, pr.expires_at,
               a.id, a.username, a.email, a.password_hash
        FROM password_resets AS pr
        JOIN admins AS a ON a.id = pr.admin_id
        WHERE pr.token_hash = ?
          AND pr.used_at IS NULL
          AND pr.expires_at > ?
        """,
        (hash_reset_token(token), utc_now_string()),
    ).fetchone()


def google_signin_configured() -> bool:
    config = current_app.config
    return bool(config["GOOGLE_CLIENT_ID"] and config["GOOGLE_CLIENT_SECRET"])


def google_redirect_uri() -> str:
    return current_app.config["GOOGLE_REDIRECT_URI"] or url_for(
        "google_callback", _external=True
    )


def google_email_allowed(email: str) -> bool:
    allowed = current_app.config["GOOGLE_ALLOWED_EMAILS"]
    return email.lower() in allowed


def unique_admin_username(db: sqlite3.Connection, email: str) -> str:
    base = re.sub(r"[^a-z0-9._-]", "", email.split("@")[0].lower())[:30]
    base = base or "google-user"
    candidate = base
    counter = 1
    while db.execute(
        "SELECT 1 FROM admins WHERE username = ?", (candidate,)
    ).fetchone():
        counter += 1
        suffix = f"-{counter}"
        candidate = base[: 30 - len(suffix)] + suffix
    return candidate


def fetch_google_json(
    url: str, data: dict[str, str] | None = None, headers: dict[str, str] | None = None
) -> dict:
    body = urlencode(data).encode("utf-8") if data is not None else None
    request_headers = {"User-Agent": "RoadWatch/1.0"}
    request_headers.update(headers or {})
    req = UrlRequest(url, data=body, headers=request_headers)
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def generate_tracking_number(db: sqlite3.Connection) -> str:
    date_part = utc_now().strftime("%Y%m%d")
    for _ in range(25):
        suffix = "".join(secrets.choice(TRACKING_ALPHABET) for _ in range(5))
        candidate = f"RW-{date_part}-{suffix}"
        exists = db.execute(
            "SELECT 1 FROM reports WHERE tracking_number = ?", (candidate,)
        ).fetchone()
        if not exists:
            return candidate
    raise RuntimeError("Could not allocate a unique tracking number.")


def get_public_stats(db: sqlite3.Connection) -> dict[str, int]:
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END), 0) AS resolved,
            COALESCE(SUM(CASE WHEN status IN ('Submitted', 'Under Review', 'In Progress')
                              THEN 1 ELSE 0 END), 0) AS open,
            COUNT(DISTINCT city) AS cities
        FROM reports
        WHERE status != 'Rejected'
        """
    ).fetchone()
    return {
        "total": row["total"] or 0,
        "resolved": row["resolved"] or 0,
        "open": row["open"] or 0,
        "cities": row["cities"] or 0,
    }


def get_admin_stats(db: sqlite3.Connection) -> dict[str, int]:
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status NOT IN ('Resolved', 'Rejected')
                              THEN 1 ELSE 0 END), 0) AS open,
            COALESCE(SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END), 0) AS resolved,
            COALESCE(SUM(CASE WHEN severity IN ('High', 'Critical')
                              AND status NOT IN ('Resolved', 'Rejected')
                              THEN 1 ELSE 0 END), 0) AS urgent
        FROM reports
        """
    ).fetchone()
    return {
        "total": row["total"] or 0,
        "open": row["open"] or 0,
        "resolved": row["resolved"] or 0,
        "urgent": row["urgent"] or 0,
    }


def render_home(form_data=None, status_code: int = 200):
    db = get_db()
    recent = db.execute(
        """
        SELECT *
        FROM reports
        WHERE status != 'Rejected'
        ORDER BY created_at DESC, id DESC
        LIMIT 3
        """
    ).fetchall()
    return (
        render_template(
            "index.html",
            form=form_data if form_data is not None else {},
            stats=get_public_stats(db),
            recent=recent,
        ),
        status_code,
    )


def _read_text(
    field: str, label: str, errors: list[str], max_length: int, required: bool = False
) -> str:
    value = (request.form.get(field) or "").strip()
    if required and not value:
        errors.append(f"{label} is required.")
    elif len(value) > max_length:
        errors.append(f"{label} must be {max_length} characters or fewer.")
    return value


def _detect_image_extension(file_storage) -> str | None:
    header = file_storage.stream.read(16)
    file_storage.stream.seek(0)

    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    return None


def save_photo(file_storage) -> str | None:
    if not file_storage or not file_storage.filename:
        return None

    extension = _detect_image_extension(file_storage)
    if extension is None:
        raise ValueError("The photo must be a JPG, PNG, GIF, or WebP image.")

    filename = f"{uuid.uuid4().hex}{extension}"
    file_storage.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename)
    return filename


def _pagination(page: int, per_page: int, total: int) -> dict[str, int | bool]:
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(max(page, 1), pages)
    offset = (page - 1) * per_page
    return {
        "page": page,
        "pages": pages,
        "total": total,
        "per_page": per_page,
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_page": page - 1,
        "next_page": page + 1,
        "start": offset + 1 if total else 0,
        "end": min(offset + per_page, total),
    }


# ---------------------------------------------------------------------------
# Request hooks and template helpers
# ---------------------------------------------------------------------------


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        expected = session.get("_csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not supplied or not hmac.compare_digest(expected, supplied):
            abort(
                400,
                description=(
                    "Your form session has expired. Go back, refresh the page, "
                    "and try again."
                ),
            )


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self'; "
        "script-src 'self'; font-src 'self'; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'self'",
    )
    if request.endpoint in {
        "login",
        "logout",
        "admin_dashboard",
        "admin_update_report",
        "account",
        "update_account_email",
        "update_account_password",
        "forgot_password",
        "reset_password",
        "google_login",
        "google_callback",
    }:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.context_processor
def inject_template_globals():
    return {
        "csrf_token": get_csrf_token,
        "statuses": STATUSES,
        "public_statuses": PUBLIC_STATUSES,
        "issue_types": ISSUE_TYPES,
        "severities": SEVERITIES,
        "severity_help": SEVERITY_HELP,
        "current_year": utc_now().year,
        "google_signin_enabled": google_signin_configured(),
    }


@app.template_filter("readable_datetime")
def readable_datetime(value: str | None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except (TypeError, ValueError):
        return value
    return parsed.strftime("%d %b %Y, %H:%M UTC")


@app.template_filter("status_slug")
def status_slug(value: str) -> str:
    return value.lower().replace(" ", "-")


@app.template_filter("initials")
def initials(value: str) -> str:
    parts = [part for part in value.split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "A"


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------


@app.get("/download")
def download_source():
    """Download the complete RoadWatch project as a ZIP archive."""
    zip_path = Path("C:/Users/C Bhaskar/Downloads/Roadwatch.zip")
    if not zip_path.exists():
        abort(404, description="The source archive is not available.")
    return send_file(
        zip_path,
        as_attachment=True,
        download_name="Roadwatch.zip",
        mimetype="application/zip",
    )


@app.get("/")
def index():
    return render_home()


@app.post("/report")
def submit_report():
    errors: list[str] = []
    reporter_name = _read_text("reporter_name", "Your name", errors, 100, True)
    reporter_email = _read_text("reporter_email", "Email address", errors, 254)
    reporter_phone = _read_text("reporter_phone", "Phone number", errors, 30)
    road_name = _read_text("road_name", "Road or street name", errors, 160, True)
    location = _read_text("location", "Location or landmark", errors, 200, True)
    city = _read_text("city", "City or area", errors, 100, True)
    issue_type = _read_text("issue_type", "Issue type", errors, 80, True)
    severity = _read_text("severity", "Severity", errors, 20, True)
    description = _read_text("description", "Description", errors, 3000, True)

    if reporter_email and not EMAIL_RE.match(reporter_email):
        errors.append("Enter a valid email address, or leave the field blank.")
    if issue_type and issue_type not in ISSUE_TYPES:
        errors.append("Choose a valid issue type.")
    if severity and severity not in SEVERITIES:
        errors.append("Choose a valid severity level.")
    if description and len(description) < 10:
        errors.append("Please describe the issue in at least 10 characters.")

    if errors:
        for message in errors:
            flash(message, "error")
        return render_home(request.form)

    db = get_db()
    photo_filename = None
    try:
        photo_filename = save_photo(request.files.get("photo"))
    except ValueError as exc:
        flash(str(exc), "error")
        return render_home(request.form)

    try:
        tracking_number = generate_tracking_number(db)
        created_at = utc_now_string()
        cursor = db.execute(
            """
            INSERT INTO reports (
                tracking_number, reporter_name, reporter_email, reporter_phone,
                road_name, location, city, issue_type, severity, description,
                photo_filename, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted', ?, ?)
            """,
            (
                tracking_number,
                reporter_name,
                reporter_email or None,
                reporter_phone or None,
                road_name,
                location,
                city,
                issue_type,
                severity,
                description,
                photo_filename,
                created_at,
                created_at,
            ),
        )
        db.execute(
            """
            INSERT INTO report_updates
                (report_id, status, note, admin_username, created_at)
            VALUES (?, 'Submitted', ?, NULL, ?)
            """,
            (
                cursor.lastrowid,
                "Report received and added to the review queue.",
                created_at,
            ),
        )
        db.commit()
    except Exception:
        db.rollback()
        if photo_filename:
            (UPLOAD_DIR / photo_filename).unlink(missing_ok=True)
        current_app.logger.exception("Could not save report")
        flash("We could not save your report. Please try again.", "error")
        return render_home(request.form, 500)

    return redirect(
        url_for("report_submitted", tracking_number=tracking_number)
    )


@app.get("/submitted/<tracking_number>")
def report_submitted(tracking_number: str):
    report = get_db().execute(
        "SELECT * FROM reports WHERE tracking_number = ?",
        (tracking_number.strip().upper(),),
    ).fetchone()
    if report is None:
        abort(404)
    return render_template("submitted.html", report=report)


@app.get("/track")
def track_report():
    tracking_number = (request.args.get("tracking_number") or "").strip().upper()
    if not tracking_number:
        flash("Enter a tracking number to continue.", "error")
        return redirect(url_for("index", _anchor="tracker"))

    exists = get_db().execute(
        "SELECT 1 FROM reports WHERE tracking_number = ?", (tracking_number,)
    ).fetchone()
    if not exists:
        flash(
            "We could not find a report with that tracking number. "
            "Check the number and try again.",
            "error",
        )
        return redirect(url_for("index", _anchor="tracker"))

    return redirect(
        url_for("report_detail", tracking_number=tracking_number)
    )


@app.get("/reports")
def public_reports():
    db = get_db()
    q = (request.args.get("q") or "").strip()[:100]
    status = (request.args.get("status") or "").strip()
    issue_type = (request.args.get("issue_type") or "").strip()
    severity = (request.args.get("severity") or "").strip()

    if status not in PUBLIC_STATUSES:
        status = ""
    if issue_type not in ISSUE_TYPES:
        issue_type = ""
    if severity not in SEVERITIES:
        severity = ""

    where = ["status != 'Rejected'"]
    params: list[str] = []
    if q:
        like = f"%{q}%"
        where.append(
            "(tracking_number LIKE ? OR road_name LIKE ? OR location LIKE ? "
            "OR city LIKE ? OR description LIKE ?)"
        )
        params.extend([like] * 5)
    if status:
        where.append("status = ?")
        params.append(status)
    if issue_type:
        where.append("issue_type = ?")
        params.append(issue_type)
    if severity:
        where.append("severity = ?")
        params.append(severity)

    where_sql = " AND ".join(where)
    total = db.execute(
        f"SELECT COUNT(*) FROM reports WHERE {where_sql}", params
    ).fetchone()[0]
    requested_page = request.args.get("page", default=1, type=int) or 1
    pagination = _pagination(requested_page, PUBLIC_PAGE_SIZE, total)
    reports = db.execute(
        f"""
        SELECT * FROM reports
        WHERE {where_sql}
        ORDER BY created_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, pagination["per_page"], (pagination["page"] - 1) * pagination["per_page"]],
    ).fetchall()

    return render_template(
        "reports.html",
        reports=reports,
        pagination=pagination,
        filters={
            "q": q,
            "status": status,
            "issue_type": issue_type,
            "severity": severity,
        },
        has_filters=bool(q or status or issue_type or severity),
    )


@app.get("/reports/<tracking_number>")
def report_detail(tracking_number: str):
    db = get_db()
    report = db.execute(
        "SELECT * FROM reports WHERE tracking_number = ?",
        (tracking_number.strip().upper(),),
    ).fetchone()
    if report is None:
        abort(404)

    updates = db.execute(
        """
        SELECT * FROM report_updates
        WHERE report_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (report["id"],),
    ).fetchall()
    maps_query = quote_plus(f"{report['location']}, {report['city']}")
    return render_template(
        "report_detail.html",
        report=report,
        updates=updates,
        maps_url=f"https://www.google.com/maps/search/?api=1&query={maps_query}",
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    next_url = request.values.get("next", "")
    if not is_safe_next_url(next_url):
        next_url = url_for("admin_dashboard")

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        admin = get_db().execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            sign_in_admin(admin)
            flash(f"Welcome back, {admin['username']}.", "success")
            return redirect(next_url)

        flash("Incorrect username or password.", "error")

    return render_template("login.html", next_url=next_url)


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin_dashboard"))


@app.get("/account")
@login_required
def account():
    # Admin sign-in has been removed; redirect to the admin workspace.
    return redirect(url_for("admin_dashboard"))


@app.post("/account/email")
@login_required
def update_account_email():
    admin = get_admin(session.get("admin_id"))
    if admin is None:
        session.clear()
        return redirect(url_for("admin_dashboard"))

    email = (request.form.get("email") or "").strip().lower()
    if email and not EMAIL_RE.match(email):
        flash("Enter a valid email address, such as name@example.com.", "error")
        return redirect(url_for("account"))

    try:
        get_db().execute(
            "UPDATE admins SET email = ? WHERE id = ?", (email or None, admin["id"])
        )
        get_db().commit()
    except sqlite3.IntegrityError:
        flash("That email address is already used by another admin.", "error")
        return redirect(url_for("account"))

    if email:
        flash(
            "Contact email saved. It is used for password resets and Google sign-in.",
            "success",
        )
    else:
        flash("Contact email removed.", "success")
    return redirect(url_for("account"))


@app.post("/account/password")
@login_required
def update_account_password():
    admin = get_admin(session.get("admin_id"))
    if admin is None:
        session.clear()
        return redirect(url_for("admin_dashboard"))

    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not check_password_hash(admin["password_hash"], current_password):
        flash("Your current password is incorrect.", "error")
        return redirect(url_for("account"))
    if new_password != confirm_password:
        flash("The new passwords do not match. Please re-enter them.", "error")
        return redirect(url_for("account"))
    if check_password_hash(admin["password_hash"], new_password):
        flash("Choose a password different from your current one.", "error")
        return redirect(url_for("account"))

    problems = password_problems(new_password, admin["username"], admin["email"] or "")
    if problems:
        flash(
            "Your new password must meet every rule: " + "; ".join(problems) + ".",
            "error",
        )
        return redirect(url_for("account"))

    get_db().execute(
        "UPDATE admins SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), admin["id"]),
    )
    get_db().commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("account"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if session.get("admin_id"):
        return redirect(url_for("account"))

    reset_link = None
    delivered = False
    shown_locally = False
    submitted = False

    if request.method == "POST":
        submitted = True
        identifier = (request.form.get("identifier") or "").strip()
        db = get_db()
        admin = db.execute(
            """
            SELECT * FROM admins
            WHERE username = ?
               OR (email IS NOT NULL AND email = ?)
            """,
            (identifier, identifier.lower()),
        ).fetchone()

        if admin is not None:
            token = create_password_reset(db, admin["id"])
            reset_link = url_for("reset_password", token=token, _external=True)
            current_app.logger.info(
                "Password reset link generated for '%s': %s",
                admin["username"],
                reset_link,
            )
            if admin["email"] and smtp_configured():
                delivered = send_password_reset_email(admin["email"], reset_link)
            shown_locally = request.remote_addr in {"127.0.0.1", "::1"} or bool(
                current_app.config["SHOW_RESET_LINK"]
            )
            if not delivered and not shown_locally:
                reset_link = None
            elif shown_locally and not delivered:
                flash(
                    "Email delivery is not configured, so the reset link is shown "
                    "below. Open it on this computer.",
                    "info",
                )
        else:
            # Same response shape as a real account to avoid revealing usernames.
            flash(
                "If that account exists, password reset instructions have been prepared.",
                "info",
            )

        if delivered:
            flash(
                "If that account exists, a reset link has been sent to its email address.",
                "info",
            )
        elif reset_link is None:
            flash(
                "If that account exists, reset instructions have been prepared. "
                "Check the account email, or ask the site owner to reset it on the "
                "RoadWatch server.",
                "info",
            )

    return render_template(
        "forgot_password.html",
        submitted=submitted,
        reset_link=reset_link,
        delivered=delivered,
        shown_locally=shown_locally,
    )


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    db = get_db()
    reset = find_password_reset(db, token)
    if reset is None:
        return (
            render_template(
                "reset_password.html",
                valid=False,
                username=None,
                token=None,
            ),
            400,
        )

    if request.method == "POST":
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if new_password != confirm_password:
            flash("The new passwords do not match. Please re-enter them.", "error")
        else:
            problems = password_problems(
                new_password, reset["username"], reset["email"] or ""
            )
            if problems:
                flash(
                    "Your new password must meet every rule: "
                    + "; ".join(problems)
                    + ".",
                    "error",
                )
            else:
                timestamp = utc_now_string()
                db.execute(
                    "UPDATE admins SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(new_password), reset["id"]),
                )
                db.execute(
                    "UPDATE password_resets SET used_at = ? WHERE id = ?",
                    (timestamp, reset["reset_id"]),
                )
                db.execute(
                    "DELETE FROM password_resets WHERE admin_id = ? AND used_at IS NULL",
                    (reset["id"],),
                )
                db.commit()
                session.clear()
                flash(
                    "Password reset complete. Sign in with your new password.",
                    "success",
                )
                return redirect(url_for("admin_dashboard"))

    return render_template(
        "reset_password.html",
        valid=True,
        username=reset["username"],
        token=token,
    )


@app.get("/auth/google")
def google_login():
    if not google_signin_configured():
        flash(
            "Google sign-in has not been configured on this RoadWatch site yet. "
            "The site owner can add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
            "info",
        )
        return redirect(url_for("admin_dashboard"))

    next_url = request.args.get("next", "")
    if not is_safe_next_url(next_url):
        next_url = url_for("admin_dashboard")

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    session["google_state"] = state
    session["google_verifier"] = verifier
    session["google_next"] = next_url

    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": google_redirect_uri(),
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    return redirect(f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}")


@app.get("/auth/google/callback")
def google_callback():
    if not google_signin_configured():
        flash("Google sign-in is not configured on this site.", "error")
        return redirect(url_for("admin_dashboard"))

    saved_state = session.pop("google_state", "")
    verifier = session.pop("google_verifier", "")
    next_url = session.pop("google_next", "") or url_for("admin_dashboard")
    if not is_safe_next_url(next_url):
        next_url = url_for("admin_dashboard")

    if request.args.get("error"):
        flash("Google sign-in was cancelled.", "info")
        return redirect(url_for("admin_dashboard"))

    state = request.args.get("state") or ""
    code = (request.args.get("code") or "").strip()
    if not saved_state or not state or not hmac.compare_digest(saved_state, state):
        abort(
            400,
            description=(
                "The Google sign-in request expired or did not match. "
                "Please start again from the sign-in page."
            ),
        )
    if not verifier or not code:
        flash("Google sign-in could not be completed. Please try again.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        token_response = fetch_google_json(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": current_app.config["GOOGLE_CLIENT_ID"],
                "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
                "redirect_uri": google_redirect_uri(),
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValueError("Google did not return an access token.")
        userinfo = fetch_google_json(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        current_app.logger.warning("Google sign-in failed: %s", exc)
        flash(
            "Google sign-in could not be completed right now. Please try again.",
            "error",
        )
        return redirect(url_for("admin_dashboard"))

    email = (userinfo.get("email") or "").strip().lower()
    google_sub = str(userinfo.get("sub") or "").strip()
    verified = userinfo.get("email_verified") in (True, "true", "True", 1)
    if not email or not google_sub or not verified:
        flash(
            "Google did not provide a verified email address for this account.",
            "error",
        )
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    admin = db.execute(
        "SELECT * FROM admins WHERE google_sub = ?", (google_sub,)
    ).fetchone()

    if admin is None:
        admin = db.execute(
            "SELECT * FROM admins WHERE email = ?", (email,)
        ).fetchone()
        if admin is not None:
            if admin["google_sub"] and admin["google_sub"] != google_sub:
                flash(
                    "That email is already linked to a different Google account.",
                    "error",
                )
                return redirect(url_for("admin_dashboard"))
            db.execute(
                "UPDATE admins SET google_sub = ?, email = ? WHERE id = ?",
                (google_sub, email, admin["id"]),
            )
            db.commit()
            admin = get_admin(admin["id"])
        elif google_email_allowed(email):
            username = unique_admin_username(db, email)
            try:
                db.execute(
                    """
                    INSERT INTO admins
                    (username, password_hash, email, google_sub, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        generate_password_hash(secrets.token_urlsafe(32)),
                        email,
                        google_sub,
                        utc_now_string(),
                    ),
                )
                db.commit()
            except sqlite3.IntegrityError:
                admin = db.execute(
                    "SELECT * FROM admins WHERE google_sub = ?", (google_sub,)
                ).fetchone()
                if admin is None:
                    flash(
                        "An account with that email already exists. Sign in with "
                        "your password, then connect Google from Account settings.",
                        "error",
                    )
                    return redirect(url_for("admin_dashboard"))
            else:
                admin = db.execute(
                    "SELECT * FROM admins WHERE google_sub = ?", (google_sub,)
                ).fetchone()
        else:
            flash(
                "That Google account is not authorized for this RoadWatch site. "
                "Ask the site owner to add your email address to the allowed list.",
                "error",
            )
            return redirect(url_for("admin_dashboard"))

    if admin is None:
        flash("Google sign-in could not find a matching account.", "error")
        return redirect(url_for("admin_dashboard"))

    sign_in_admin(admin)
    flash(f"Signed in with Google as {admin['username']}.", "success")
    return redirect(next_url)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------


@app.get("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    q = (request.args.get("q") or "").strip()[:100]
    status = (request.args.get("status") or "").strip()
    issue_type = (request.args.get("issue_type") or "").strip()
    severity = (request.args.get("severity") or "").strip()

    if status not in STATUSES:
        status = ""
    if issue_type not in ISSUE_TYPES:
        issue_type = ""
    if severity not in SEVERITIES:
        severity = ""

    where = ["1 = 1"]
    params: list[str] = []
    if q:
        like = f"%{q}%"
        where.append(
            "(tracking_number LIKE ? OR reporter_name LIKE ? OR reporter_email LIKE ? "
            "OR road_name LIKE ? OR location LIKE ? OR city LIKE ?)"
        )
        params.extend([like] * 6)
    if status:
        where.append("status = ?")
        params.append(status)
    if issue_type:
        where.append("issue_type = ?")
        params.append(issue_type)
    if severity:
        where.append("severity = ?")
        params.append(severity)

    where_sql = " AND ".join(where)
    total = db.execute(
        f"SELECT COUNT(*) FROM reports WHERE {where_sql}", params
    ).fetchone()[0]
    requested_page = request.args.get("page", default=1, type=int) or 1
    pagination = _pagination(requested_page, ADMIN_PAGE_SIZE, total)
    reports = db.execute(
        f"""
        SELECT * FROM reports
        WHERE {where_sql}
        ORDER BY
            CASE status
                WHEN 'Submitted' THEN 0
                WHEN 'Under Review' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Resolved' THEN 3
                ELSE 4
            END,
            created_at DESC,
            id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, pagination["per_page"], (pagination["page"] - 1) * pagination["per_page"]],
    ).fetchall()

    return render_template(
        "admin/dashboard.html",
        reports=reports,
        stats=get_admin_stats(db),
        pagination=pagination,
        filters={
            "q": q,
            "status": status,
            "issue_type": issue_type,
            "severity": severity,
        },
        has_filters=bool(q or status or issue_type or severity),
    )


@app.post("/admin/reports/<int:report_id>/status")
@login_required
def admin_update_report(report_id: int):
    db = get_db()
    report = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if report is None:
        abort(404)

    status = (request.form.get("status") or "").strip()
    public_note = (request.form.get("public_note") or "").strip()
    admin_note = (request.form.get("admin_note") or "").strip()

    if status not in STATUSES:
        flash("Choose a valid status.", "error")
        return redirect(_admin_return_url())
    if len(public_note) > 1000:
        flash("The public update note must be 1,000 characters or fewer.", "error")
        return redirect(_admin_return_url())
    if len(admin_note) > 2000:
        flash("The internal note must be 2,000 characters or fewer.", "error")
        return redirect(_admin_return_url())

    status_changed = status != report["status"]
    note_changed = public_note != ""
    internal_note_changed = admin_note != (report["admin_note"] or "")

    if not status_changed and not note_changed and not internal_note_changed:
        flash("No changes were made to this report.", "info")
        return redirect(_admin_return_url())

    timestamp = utc_now_string()
    try:
        db.execute(
            """
            UPDATE reports
            SET status = ?, admin_note = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, admin_note or None, timestamp, report_id),
        )
        if status_changed or note_changed:
            history_note = public_note or f"Status updated to {status}."
            db.execute(
                """
                INSERT INTO report_updates
                    (report_id, status, note, admin_username, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    status,
                    history_note,
                    session.get("admin_username", "admin"),
                    timestamp,
                ),
            )
        db.commit()
    except Exception:
        db.rollback()
        current_app.logger.exception("Could not update report %s", report_id)
        flash("The report could not be updated. Please try again.", "error")
        return redirect(_admin_return_url())

    flash(f"Report {report['tracking_number']} has been updated.", "success")
    return redirect(_admin_return_url())


def _admin_return_url() -> str:
    target = request.form.get("next", "")
    if is_safe_next_url(target):
        return target
    return url_for("admin_dashboard")


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


def _error_page(status_code: int, title: str, message: str):
    return (
        render_template(
            "error.html",
            status_code=status_code,
            error_title=title,
            error_message=message,
        ),
        status_code,
    )


@app.errorhandler(400)
def bad_request(error):
    description = getattr(error, "description", None) or (
        "The request could not be understood."
    )
    return _error_page(400, "That request needs another look", description)


@app.errorhandler(404)
def not_found(_error):
    return _error_page(
        404,
        "Report not found",
        "The page or report you are looking for does not exist. "
        "Check the tracking number and try again.",
    )


@app.errorhandler(413)
def file_too_large(_error):
    return _error_page(
        413,
        "Photo is too large",
        "Please upload a photo smaller than 8 MB and submit the form again.",
    )


@app.errorhandler(500)
def server_error(_error):
    return _error_page(
        500,
        "Something went wrong",
        "RoadWatch hit an unexpected problem. Please try again in a moment.",
    )


# ---------------------------------------------------------------------------
# CLI commands and local server
# ---------------------------------------------------------------------------


@app.cli.command("init-db")
def init_db_command():
    """Create the database tables if they do not exist."""
    init_db()
    click.echo(f"Initialized database at {app.config['DATABASE']}")


@app.cli.command("create-admin")
@click.option("--username", prompt="Admin username")
@click.option(
    "--password",
    prompt="Password",
    hide_input=True,
    confirmation_prompt=True,
)
def create_admin_command(username: str, password: str):
    """Create an admin, or reset the password of an existing admin."""
    username = username.strip()
    if not username:
        raise click.ClickException("Username cannot be blank.")
    if len(password) < 8:
        raise click.ClickException("Use a password with at least 8 characters.")

    db = get_db()
    existing = db.execute(
        "SELECT id FROM admins WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE admins SET password_hash = ? WHERE id = ?",
            (generate_password_hash(password), existing["id"]),
        )
        action = "Updated"
    else:
        db.execute(
            "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), utc_now_string()),
        )
        action = "Created"
    db.commit()
    click.echo(f"{action} admin '{username}'.")


initialize_app()


if __name__ == "__main__":
    app.run(
        # Bind to every interface so phones and other PCs on the LAN can reach
        # the site. Set HOST=127.0.0.1 to restrict it to this computer only.
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
