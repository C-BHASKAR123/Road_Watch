# RoadWatch

RoadWatch is a small community road-reporting web app built with Flask and SQLite.
Residents can report potholes, damaged surfaces, waterlogging, broken footpaths,
signage problems, and streetlight issues. Every submission receives a tracking
number and a public status timeline. Administrators get a private review queue
for triage, public updates, and internal notes.

## Features

- Public report form with validation and optional photo upload
- Unique tracking numbers in the form `RW-YYYYMMDD-XXXXX`
- Tracking lookup and a confirmation page that is safe to bookmark
- Public report directory with search, status, issue, and severity filters
- Report detail pages with location, severity, photo, and status timeline
- Administrator login with hashed passwords and protected routes
- Account settings with current-password check, new password, and re-entry
- Strong password policy enforced on password changes and resets
- Forgot-password flow with one-time, expiring reset links
- Optional Google sign-in through Google OAuth 2.0
- Admin queue with priority ordering, filters, public updates, and private notes
- CSRF protection on every form, security headers, and content-type validation
- Responsive, accessible interface with no frontend build step
- SQLite database and upload directories created automatically

## Quick start

### 1. Create a virtual environment

Windows PowerShell:

```powershell
cd roadwatch
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script, run this once for the current shell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

macOS or Linux:

```bash
cd roadwatch
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

Open <http://127.0.0.1:5000>.

On first start, RoadWatch creates:

- `instance/roadwatch.db` — the SQLite database
- `instance/.secret_key` — a local session-signing key when `SECRET_KEY` is not set
- `static/uploads/` — uploaded photos

### 3. Sign in as an administrator

The first account is seeded only when the database has no administrators:

| Setting | Default |
| --- | --- |
| Username | `admin` |
| Password | `roadwatch123` |

These defaults are for local development only. Set `ROADWATCH_ADMIN_USERNAME` and
`ROADWATCH_ADMIN_PASSWORD` **before the first run**, or use the CLI command below
to change the password immediately:

```bash
flask --app app create-admin
```

The command updates the password when the username already exists and creates the
account when it does not.

## Configuration

Configuration is read from environment variables. No `.env` file is loaded by
default, so set these in your shell, process manager, or hosting platform.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Generated file | Signs session cookies. Set a long random value in production. |
| `ROADWATCH_DATABASE` | `instance/roadwatch.db` | SQLite database path. Relative paths resolve from the project folder. |
| `ROADWATCH_ADMIN_USERNAME` | `admin` | First-run admin username. Ignored once an admin exists. |
| `ROADWATCH_ADMIN_PASSWORD` | `roadwatch123` | First-run admin password. Ignored once an admin exists. |
| `ROADWATCH_COOKIE_SECURE` | `0` | Set to `1` when serving over HTTPS. |
| `ROADWATCH_RESET_TTL_MINUTES` | `30` | Lifetime of a password reset link. |
| `ROADWATCH_SHOW_RESET_LINK` | `0` | Set to `1` to show reset links on any device. Otherwise links are shown only on localhost. |
| `ROADWATCH_SMTP_HOST` | empty | SMTP server for password reset email. |
| `ROADWATCH_SMTP_PORT` | `587` | SMTP port. |
| `ROADWATCH_SMTP_USERNAME` | empty | SMTP username. |
| `ROADWATCH_SMTP_PASSWORD` | empty | SMTP password or app password. |
| `ROADWATCH_SMTP_FROM` | username | From address on reset emails. |
| `ROADWATCH_SMTP_SSL` | `0` | Set to `1` for implicit TLS (usually port 465). |
| `ROADWATCH_SMTP_STARTTLS` | `1` | Set to `0` to disable STARTTLS (usually port 25). |
| `GOOGLE_CLIENT_ID` | empty | Google OAuth client ID. |
| `GOOGLE_CLIENT_SECRET` | empty | Google OAuth client secret. |
| `GOOGLE_REDIRECT_URI` | generated | Exact authorized redirect URI, when it differs from the request host. |
| `ROADWATCH_GOOGLE_ALLOWED_EMAILS` | empty | Comma-separated emails allowed to create an admin account through Google. |
| `HOST` | `0.0.0.0` | Host used by `python app.py`. Use `127.0.0.1` to restrict access to this computer only. |
| `PORT` | `5000` | Port used by `python app.py`. |
| `FLASK_DEBUG` | `0` | Set to `1` for the Flask debug reloader. Never enable in production. |

Windows PowerShell example:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
$env:ROADWATCH_ADMIN_PASSWORD = "replace-with-a-strong-password"
$env:ROADWATCH_COOKIE_SECURE = "0"
python app.py
```

### Password reset email

Password reset works without email on the server computer: when SMTP is not
configured, the one-time link is shown on the reset page only for requests from
`127.0.0.1`/`::1`, and it is also written to the server log. To deliver links to
other devices, configure SMTP:

```powershell
$env:ROADWATCH_SMTP_HOST = "smtp.example.com"
$env:ROADWATCH_SMTP_PORT = "587"
$env:ROADWATCH_SMTP_USERNAME = "alerts@example.com"
$env:ROADWATCH_SMTP_PASSWORD = "your-app-password"
$env:ROADWATCH_SMTP_FROM = "RoadWatch <alerts@example.com>"
```

Save a contact email under **Account settings** first. The link expires after
30 minutes and stops working after one successful reset.

### Google sign-in setup

1. Open the Google Cloud Console, create an OAuth client ID of type **Web
   application**, and add these authorized redirect URIs:
   - `http://127.0.0.1:5000/auth/google/callback`
   - `http://BHASKAR.local:5000/auth/google/callback` (or your LAN hostname)
   - Your HTTPS callback URL when deployed
2. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
3. Optionally set `ROADWATCH_GOOGLE_ALLOWED_EMAILS` to let listed Google
   accounts create an admin account automatically.
4. Save the same email in **Account settings**, sign out, then choose
   **Continue with Google** to link an existing account.

Without credentials the Google button remains visible but reports that setup is
incomplete. Google sign-in requires an internet connection and a verified Google
email address.

## Routes

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | Public | Homepage, statistics, report form, tracker |
| `POST` | `/report` | Public | Validate and save a report |
| `GET` | `/submitted/<tracking_number>` | Public | Submission confirmation |
| `GET` | `/track` | Public | Tracking-number lookup |
| `GET` | `/reports` | Public | Searchable public report list |
| `GET` | `/reports/<tracking_number>` | Public | Report details and timeline |
| `GET, POST` | `/login` | Public | Administrator sign-in |
| `GET` | `/auth/google` | Public | Start Google OAuth sign-in |
| `GET` | `/auth/google/callback` | Public | Finish Google OAuth sign-in |
| `GET, POST` | `/forgot-password` | Public | Request a one-time reset link |
| `GET, POST` | `/reset-password/<token>` | Public | Choose a new password with a valid token |
| `POST` | `/logout` | Admin | End the administrator session |
| `GET` | `/account` | Admin | Account settings and password change |
| `POST` | `/account/email` | Admin | Save the contact email |
| `POST` | `/account/password` | Admin | Change the password |
| `GET` | `/admin` | Admin | Report queue and filters |
| `POST` | `/admin/reports/<id>/status` | Admin | Status, public note, and private note update |

Reports with the `Rejected` status are hidden from the public directory but remain
reachable by their tracking number and visible in the admin queue.

## Status workflow

```text
Submitted -> Under Review -> In Progress -> Resolved
                    \-> Rejected
```

Changing a status in the admin dashboard adds an entry to the public timeline.
An administrator can also add a public note without changing the status. Internal
notes are visible only inside the admin queue. Reporter names, email addresses,
and phone numbers are never displayed on public pages.

## Data and uploads

The SQLite schema is created automatically. It has four tables:

- `reports` — report content, private contact details, current status, private note
- `report_updates` — public status timeline and update notes
- `admins` — usernames, password hashes, contact email, and linked Google account
- `password_resets` — hashed, expiring, single-use reset tokens

Older databases are migrated in place: `email` and `google_sub` columns are
added to `admins` and the reset table is created on startup.

Photos are optional. Accepted formats are JPG, PNG, GIF, and WebP, detected by
file signature rather than file extension. The request limit is 8.5 MB; the photo
guidance in the form is 8 MB. Files are stored under randomized names in
`static/uploads/`.

Back up `instance/roadwatch.db` and `static/uploads/` together. Those two paths
contain all persistent application data.

## CLI commands

```bash
# Create database tables if needed
flask --app app init-db

# Create an admin, or reset an existing admin's password
flask --app app create-admin
```

## Security notes

RoadWatch includes:

- Salted password hashes through Werkzeug
- Strong password policy: 12+ characters, upper and lower case, number, symbol
- Reset tokens stored as SHA-256 hashes, single use, and expiring
- Google OAuth state checks plus PKCE (S256)
- CSRF tokens on all POST forms
- Parameterized SQL queries
- Server-side validation for all fields
- Image signature checks and randomized upload names
- HttpOnly, SameSite=Lax session cookies
- Content Security Policy and other security headers
- Private/internal admin notes that are never rendered publicly
- Generic login and reset messages that do not reveal whether an account exists

Before exposing RoadWatch to the public internet:

1. Set a strong `SECRET_KEY` and a strong administrator password.
2. Serve over HTTPS and set `ROADWATCH_COOKIE_SECURE=1`.
3. Put a production WSGI server behind a reverse proxy.
4. Add rate limiting for report submissions and login attempts.
5. Add automated backups and log retention.
6. Consider a moderation workflow for uploaded images and public notes.
7. Review the privacy and retention requirements that apply in your region.

The built-in Flask server is for development only. Example production commands:

```bash
# Linux/macOS
pip install gunicorn
gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
```

```powershell
# Windows
pip install waitress
waitress-serve --listen=0.0.0.0:8000 app:app
```

## Project structure

```text
roadwatch/
├── app.py                    # Flask app, routes, database, CLI commands
├── requirements.txt          # Python dependency
├── README.md
├── .gitignore
├── instance/                 # Created at runtime
│   ├── roadwatch.db
│   └── .secret_key
├── static/
│   ├── css/
│   │   └── style.css
│   ├── images/
│   │   ├── .gitkeep
│   │   └── roadwatch-logo.svg
│   ├── js/
│   │   └── app.js
│   └── uploads/              # Created/populated at runtime
│       └── .gitkeep
└── templates/
    ├── base.html
    ├── index.html
    ├── submitted.html
    ├── reports.html
    ├── report_detail.html
    ├── login.html
    ├── error.html
    └── admin/
        └── dashboard.html
```

## Troubleshooting

**The admin password does not match the environment variable.**
The environment variables are used only when the `admins` table is empty. Reset
the password with `flask --app app create-admin` or remove the database and start
again.

**Other devices cannot open the site.**
Start the server with `HOST=0.0.0.0` (the default and the launchers already do
this), then allow inbound TCP port 5000 in Windows Firewall for both Private and
Public networks. On the phone or other PC, open `http://<this-pc-ipv4>:5000`
(for example `http://192.168.3.112:5000`), not `127.0.0.1` and preferably not a
`.local` hostname. Some shared or guest Wi-Fi networks isolate clients from each
other; in that case connect the devices to a phone hotspot or to a Wi-Fi network
that allows client-to-client traffic. On Windows, `start-hotspot.ps1` can turn
the PC into a hotspot when the adapter supports it, and `watch-hotspot.ps1`
turns it back on if Windows shuts it down after a period with no clients.

**A photo will not upload.**
Check that it is a real JPG, PNG, GIF, or WebP and is under 8 MB. Renaming another
file type to `.jpg` will not pass validation.

**The database is locked.**
Stop other app processes that are using the same database. SQLite is configured
for normal local traffic; use a server database if you expect many concurrent
writers.

**Styles or uploads are missing after deployment.**
Make sure the whole `static/` directory is deployed and writable by the app user.
Keep `instance/` and `static/uploads/` on persistent storage.
