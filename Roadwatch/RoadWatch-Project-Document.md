# RoadWatch

## Road Issue Reporting and Tracking System

**Project Documentation and Complete Source Code**

| | |
| --- | --- |
| Document | Technical documentation and source listings |
| Application version | 1.0 |
| Platform | Windows 11, Python 3.13, Flask 3.1.2, SQLite |
| Prepared for | Site administrator |
| Date | 05 November 2026 |

---

## Table of Contents

1. Abstract
2. Introduction
3. Objectives
4. Scope and Features
5. Technology Stack
6. System Architecture
7. Project Structure
8. Database Design
9. Route Reference
10. Report Status Workflow
11. Security Design
12. Environment Configuration
13. Running the Application
14. Access from Phones and Other PCs
15. Long-Term Reliability Setup
16. Testing and Verification
17. Limitations and Future Scope
18. Conclusion
19. Source Code Listings
Appendix A. Daily Operation Quick Card

## Abstract

RoadWatch is a web application for reporting and tracking road problems such as potholes, waterlogging, broken footpaths, damaged signage and faulty streetlights. A citizen opens the site from a phone or computer, describes the problem, optionally attaches a photograph, and receives a unique tracking number. The administrator signs in to a protected workspace, reviews the queue, updates the status and records notes, and those changes appear on the public timeline.

The application is written in Python with the Flask web framework and uses SQLite for storage. It is intentionally small and dependable: Flask is the only third-party runtime package, the database is a single file, and the interface is server-rendered HTML with a little JavaScript for convenience. The system includes strong-password rules, a password change screen, a one-time password reset flow, Google sign-in, CSRF protection, upload validation, security headers and a complete audit timeline for every report.

RoadWatch is designed to run on a single Windows laptop and to be reachable from other devices on the same network. A PowerShell watchdog restarts the web server and the Windows mobile hotspot automatically, and the power settings keep the laptop awake while it is plugged in. This document explains the design and operation of the system and then provides the complete source code.

## 1. Introduction

### 1.1 Background

Road defects are usually reported through phone calls, informal messages or verbal complaints. These channels rarely produce a reference number, a written record or a visible status, so citizens cannot tell whether anything happened and administrators cannot easily demonstrate progress.

### 1.2 Problem statement

The administrator needs a simple system that can:

- accept structured reports from the public, including a photo and location;
- give every report a unique, shareable tracking number;
- keep a public list of reports and a timeline of official updates;
- protect the administrator workspace with a strong password and recovery options;
- stay available for months on ordinary hardware without manual restarts;
- be usable from the laptop itself, from phones and from other PCs on the same network.

### 1.3 Proposed solution

RoadWatch implements those needs as a compact Flask application. Citizens use a public form and public tracking pages. The administrator uses a separate sign-in area with a queue, filters, status changes and notes. SQLite stores reports, updates, administrator accounts and password-reset tokens. Windows helper scripts start the server at sign-in and keep both the server and the hotspot alive.

### 1.4 Deployment context

The reference deployment is a single Windows 11 laptop with an Intel Wi-Fi 6E adapter. The laptop is connected to an external Wi-Fi network for internet access and also broadcasts its own hotspot, named RoadWatch, for nearby phones and PCs. The site is served over plain HTTP inside the local network. No public internet exposure is required.

## 2. Objectives

- Provide a clear, mobile-friendly public reporting form.
- Store reports reliably with validation and optional photo evidence.
- Issue unique tracking numbers and show an official status timeline.
- Give the administrator an efficient queue with filters and search.
- Enforce strong administrator passwords and provide self-service recovery.
- Support Google sign-in without adding third-party Python dependencies.
- Keep personal data and administrative notes separate from public data.
- Survive reboots and long idle periods with automatic recovery.
- Remain easy to understand, deploy and maintain on one computer.

## 3. Scope and Features

### 3.1 Public features

- Homepage with live statistics and a report form.
- Issue types: pothole, damaged road surface, waterlogging, broken footpath, missing or damaged signage, streetlight problem, other.
- Severity levels: Low, Medium, High and Critical, each with a short explanation.
- Reporter name, optional email and phone, road name, location, city and description.
- Optional photograph, validated by content and limited to 8 MB.
- Unique tracking number in the form RW-YYYYMMDD-XXXXX.
- Submission confirmation page.
- Tracking lookup by number.
- Searchable, paginated public report list.
- Public report detail page with a status timeline and official notes.

### 3.2 Administrator features

- Protected dashboard with totals for all, open, resolved and urgent reports.
- Filters for status, severity and issue type, plus text search.
- Pagination and sorting by newest first.
- Status workflow: Submitted, Under Review, In Progress, Resolved, Rejected.
- Public note shown on the report timeline.
- Private note visible only to the administrator.
- Automatic timeline entry for every status change.
- Rejected reports are hidden from the public directory but remain accessible by tracking number and visible in the admin queue.

### 3.3 Account and authentication features

- Sign-in with username and password.
- Strong-password policy enforced on creation and change.
- Confirm-password field on password change and reset.
- Contact email saved in account settings.
- Forgot-password flow with a single-use, 30-minute reset link.
- Optional email delivery over SMTP; local fallback for the server computer.
- Continue with Google using OAuth 2.0 with PKCE and state validation.
- Automatic linking of a Google account by saved email, or account creation for allow-listed emails only.
- Session lifetime of 12 hours, HttpOnly and SameSite cookies, optional Secure flag.

### 3.4 Reliability and deployment features

- Listens on all network interfaces by default.
- Windows Firewall rule for inbound TCP port 5000.
- Automatic start at Windows sign-in.
- Server watchdog that restarts Flask when port 5000 stops responding.
- Hotspot watchdog that switches the RoadWatch hotspot back on.
- Power settings that prevent sleep on AC power and keep the lid-close action as do nothing.
- Rotating watchdog log and an append-only server log.

## 4. Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Language | Python 3.13 | Application logic |
| Web framework | Flask 3.1.2 | Routing, templates, sessions |
| Templates | Jinja2 (bundled with Flask) | Server-rendered HTML |
| Database | SQLite 3 | Reports, updates, admins, reset tokens |
| Password hashing | Werkzeug security helpers | Salted one-way password hashes |
| Front end | HTML5, CSS3, vanilla JavaScript | Responsive public and admin interface |
| Email | Python smtplib and email.message | Password reset delivery |
| Google sign-in | Python standard library urllib | OAuth 2.0 authorization code flow with PKCE |
| Windows automation | PowerShell and VBScript | Startup, hotspot and watchdog |
| Packaging | Compress-Archive | Downloadable ZIP build |

The only third-party runtime dependency is Flask. Everything else is part of the Python standard library or the operating system.

## 5. System Architecture

```text
+---------------------+          HTTP           +---------------------------+
| Phone / other PC    | ----------------------> |                           |
| (RoadWatch hotspot) |                         |   Flask application       |
+---------------------+                         |   app.py                  |
                                                |                           |
+---------------------+          HTTP           |   - public routes         |
| Administrator PC    | ----------------------> |   - admin routes          |
| 127.0.0.1:5000      |                         |   - auth routes           |
+---------------------+                         +------------+--------------+
                                                             |
                        +------------------------------------+-------------------+
                        |                                    |                   |
                        v                                    v                   v
              instance/roadwatch.db                static/uploads/        templates/ + static/
              (SQLite, WAL mode)                   (report photos)        (UI assets)
                        ^
                        |
              +---------+----------+
              | watch-roadwatch.ps1|
              | every 20 seconds   |
              | - restart server   |
              | - restore hotspot  |
              +--------------------+
```

### 5.1 Request lifecycle

1. The browser requests a page over HTTP from the Flask development server.
2. Flask matches the route and runs the view function.
3. The view reads or writes SQLite through helper functions.
4. Jinja2 renders a template with the current data and CSRF token.
5. An after-request hook adds security headers and cache rules.
6. Photos are served from `static/uploads/` and interface assets from `static/`.

### 5.2 Data storage

All persistent data lives inside the project folder. The SQLite database is stored in `instance/roadwatch.db`, uploaded photos in `static/uploads/`, and the session signing key in `instance/.secret_key`. The database uses write-ahead logging so readers are not blocked by writers. Foreign keys are enabled on every connection.

## 6. Project Structure

```text
Roadwatch/
|-- app.py                     Main application: routes, database, auth, CLI
|-- requirements.txt           Python dependencies (Flask)
|-- README.md                  Setup and reference documentation
|-- .gitignore                 Files excluded from version control
|-- start.cmd                  Foreground launcher for local use
|-- start-hidden.vbs           Silent launcher used at Windows sign-in
|-- start-hotspot.ps1          One-shot hotspot starter
|-- watch-roadwatch.ps1        Combined server and hotspot watchdog
|-- watch-hotspot.ps1          Legacy hotspot-only watchdog (superseded)
|-- instance/                  Created at runtime
|   |-- roadwatch.db           SQLite database
|   `-- .secret_key            Generated session signing key
|-- static/
|   |-- css/style.css          Complete responsive stylesheet
|   |-- js/app.js              Small progressive-enhancement script
|   |-- images/roadwatch-logo.svg
|   `-- uploads/               Uploaded report photos
|-- templates/
|   |-- base.html              Shared layout and navigation
|   |-- index.html             Homepage, statistics and report form
|   |-- submitted.html         Submission confirmation
|   |-- reports.html           Public report directory
|   |-- report_detail.html     Public report and timeline
|   |-- login.html             Administrator sign-in
|   |-- account.html           Account settings and password change
|   |-- forgot_password.html   Reset request form
|   |-- reset_password.html    New password form
|   |-- error.html             Friendly error page
|   `-- admin/dashboard.html   Administrator queue
|-- server.log                 Server output (runtime)
|-- watchdog.log               Watchdog activity (runtime)
`-- hotspot.log                Legacy hotspot log (runtime)
```

The `instance/` folder, uploaded photos, log files and the `.venv/` virtual environment are runtime data and are not part of the distributable source package.

## 7. Database Design

### 7.1 admins

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER | Primary key, auto-increment |
| username | TEXT | Unique, case-insensitive |
| password_hash | TEXT | Salted one-way hash |
| email | TEXT | Optional contact email, unique when set |
| google_sub | TEXT | Optional Google subject identifier, unique when set |
| created_at | TEXT | UTC timestamp |

### 7.2 reports

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER | Primary key, auto-increment |
| tracking_number | TEXT | Unique public reference |
| reporter_name | TEXT | Required |
| reporter_email | TEXT | Optional |
| reporter_phone | TEXT | Optional |
| road_name | TEXT | Required |
| location | TEXT | Required landmark or address |
| city | TEXT | Required |
| issue_type | TEXT | One of the fixed issue types |
| severity | TEXT | Low, Medium, High or Critical |
| description | TEXT | Required free text |
| photo_filename | TEXT | Optional file name in static/uploads |
| status | TEXT | Defaults to Submitted |
| admin_note | TEXT | Private administrator note |
| created_at | TEXT | UTC timestamp |
| updated_at | TEXT | UTC timestamp |

Indexes exist on status and on created_at descending, which support the queue filters and newest-first ordering.

### 7.3 report_updates

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER | Primary key, auto-increment |
| report_id | INTEGER | Foreign key to reports, cascade delete |
| status | TEXT | Status at the time of the update |
| note | TEXT | Optional public note |
| admin_username | TEXT | Who made the change |
| created_at | TEXT | UTC timestamp |

This table is the audit trail shown as the public timeline. A row is written when a report is created and whenever the administrator changes a status.

### 7.4 password_resets

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER | Primary key, auto-increment |
| admin_id | INTEGER | Foreign key to admins, cascade delete |
| token_hash | TEXT | SHA-256 hash of the emailed token |
| expires_at | TEXT | UTC expiry, 30 minutes by default |
| used_at | TEXT | Set when the link is consumed |
| created_at | TEXT | UTC timestamp |

Only the hash is stored, so a copy of the database cannot be used to reset a password. A reset token stops working after one successful use or when it expires.

### 7.5 Migration and integrity

The schema is created with `CREATE TABLE IF NOT EXISTS`. Columns added after the first release, such as `email` and `google_sub`, are added in place with `ALTER TABLE` when missing. Unique indexes on email and Google subject are created only after that migration, so an older database keeps working. Foreign keys and WAL journaling are enabled for every connection.

## 8. Route Reference

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | / | Public | Homepage, statistics, report form and tracker |
| POST | /report | Public | Validate and save a report |
| GET | /submitted/<tracking_number> | Public | Submission confirmation |
| GET | /track | Public | Tracking-number lookup |
| GET | /reports | Public | Searchable public report list |
| GET | /reports/<tracking_number> | Public | Report details and timeline |
| GET, POST | /login | Public | Administrator sign-in |
| GET | /auth/google | Public | Start Google OAuth sign-in |
| GET | /auth/google/callback | Public | Finish Google OAuth sign-in |
| GET, POST | /forgot-password | Public | Request a one-time reset link |
| GET, POST | /reset-password/<token> | Public | Choose a new password |
| POST | /logout | Admin | End the administrator session |
| GET | /account | Admin | Account settings and password change |
| POST | /account/email | Admin | Save the contact email |
| POST | /account/password | Admin | Change the password |
| GET | /admin | Admin | Report queue and filters |
| POST | /admin/reports/<id>/status | Admin | Status, public note and private note |

All POST routes require a valid CSRF token tied to the browser session.

## 9. Report Status Workflow

| Status | Meaning | Visible publicly |
| --- | --- | --- |
| Submitted | Received but not yet reviewed | Yes |
| Under Review | Being checked by the administrator | Yes |
| In Progress | Repair or action is underway | Yes |
| Resolved | The problem has been fixed | Yes |
| Rejected | Not a valid or actionable report | Hidden from the directory, reachable by tracking number |

A new report starts as Submitted and immediately receives its first timeline entry. Each administrator update writes another timeline entry containing the new status, the public note and the username. The private note is stored on the report and is never shown on public pages.

## 10. Security Design

### 10.1 Authentication and sessions

Administrators sign in with a username and password. On success the session is cleared, the administrator identifier and username are stored, and the session is marked permanent with a 12-hour lifetime. Cookies are HttpOnly and SameSite=Lax. The Secure flag can be enabled with an environment variable when the site is served over HTTPS. Admin pages are protected by a decorator that redirects unauthenticated visitors to the sign-in page and returns them to the requested page afterwards. Only same-site next addresses are accepted.

### 10.2 Password policy

A password must contain at least 12 characters, an uppercase letter, a lowercase letter, a number and a symbol. It must not be a common password, and it must not contain the username, the local part of the email address or the word roadwatch. The same rules apply to password changes and password resets, and both forms require the new password to be entered twice. Passwords are stored only as salted one-way hashes produced by Werkzeug.

### 10.3 CSRF protection

Every POST request must include the session CSRF token in a hidden form field. A before-request hook compares the expected and supplied values with a constant-time comparison and rejects missing or stale tokens with a friendly error page. The token is generated with a cryptographically secure random source and is stored in the session.

### 10.4 Uploaded files

Photos are optional and limited to 8 MB. The application checks the file signature rather than trusting the file extension, and accepts only JPEG, PNG, GIF and WebP. Stored files receive a random name, so a malicious file name cannot overwrite another file or escape the upload directory. The overall request limit is 8.5 MB.

### 10.5 Password reset

A reset request creates a random URL-safe token and stores only its SHA-256 hash, together with a 30-minute expiry. The raw token appears only in the reset link. A link can be used once; afterwards `used_at` is set and any later attempt is rejected. When SMTP is configured, the link is emailed to the saved contact address. Without SMTP, the link is shown only to requests from the server computer itself and is written to the server log. Responses avoid revealing whether an account exists.

### 10.6 Google sign-in

Google sign-in uses the OAuth 2.0 authorization code flow implemented with the Python standard library. The application generates a state value and a PKCE verifier, sends the SHA-256 challenge, and validates the returned state before exchanging the code. It then reads the verified profile from Google's userinfo endpoint. An existing administrator is linked when the Google email matches the saved contact email. A new administrator is created only when the email is listed in `ROADWATCH_GOOGLE_ALLOWED_EMAILS`. Without credentials, the button remains visible but explains that setup is incomplete.

### 10.7 HTTP security headers

Every response includes a content security policy limited to same-origin resources, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, a strict-origin referrer policy and a permissions policy that disables camera, microphone and geolocation. Administrative and authentication responses are marked `Cache-Control: no-store`.

### 10.8 Operational recommendations

- Change the default administrator password immediately after the first sign-in.
- Keep `instance/.secret_key` private and back it up with the database.
- Do not expose this development server directly to the public internet. Use HTTPS and a production WSGI server behind a reverse proxy if public access is required.
- Restrict physical and network access to the laptop.
- Back up the database and the uploads folder regularly.

## 11. Environment Configuration

Configuration is read from environment variables. No `.env` file is loaded automatically. The defaults are suitable for local use; the settings below are available when needed.

| Variable | Default | Purpose |
| --- | --- | --- |
| SECRET_KEY | Generated file | Signs session cookies |
| ROADWATCH_DATABASE | instance/roadwatch.db | SQLite database path |
| ROADWATCH_ADMIN_USERNAME | admin | First-run admin username |
| ROADWATCH_ADMIN_PASSWORD | roadwatch123 | First-run admin password |
| ROADWATCH_COOKIE_SECURE | 0 | Set to 1 when serving over HTTPS |
| ROADWATCH_RESET_TTL_MINUTES | 30 | Lifetime of a reset link |
| ROADWATCH_SHOW_RESET_LINK | 0 | Show reset links on any device |
| ROADWATCH_SMTP_HOST | empty | SMTP server for reset email |
| ROADWATCH_SMTP_PORT | 587 | SMTP port |
| ROADWATCH_SMTP_USERNAME | empty | SMTP username |
| ROADWATCH_SMTP_PASSWORD | empty | SMTP password or app password |
| ROADWATCH_SMTP_FROM | username | From address on reset emails |
| ROADWATCH_SMTP_SSL | 0 | Implicit TLS, usually port 465 |
| ROADWATCH_SMTP_STARTTLS | 1 | Set to 0 to disable STARTTLS |
| GOOGLE_CLIENT_ID | empty | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | empty | Google OAuth client secret |
| GOOGLE_REDIRECT_URI | generated | Exact authorized redirect URI |
| ROADWATCH_GOOGLE_ALLOWED_EMAILS | empty | Emails allowed to create an account via Google |
| HOST | 0.0.0.0 | Bind address for python app.py |
| PORT | 5000 | Port for python app.py |
| FLASK_DEBUG | 0 | Enables the debug reloader; never use in production |

## 12. Running the Application

### 12.1 Requirements

- Windows 10 or 11, or any system with Python 3.10 or newer.
- Python 3.13 is recommended and is used by the reference deployment.
- Flask 3.1.2, installed from `requirements.txt`.
- About 100 MB of free disk space for the virtual environment and data.

### 12.2 First run

```powershell
cd "C:\Users\C Bhaskar\Documents\Default Project\Roadwatch"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The server prints the addresses it is listening on. Open `http://127.0.0.1:5000` on the laptop. The database, secret key and upload folder are created automatically on first use.

### 12.3 Default administrator account

On an empty database the application creates one administrator:

- Username: `admin`
- Password: `roadwatch123`

Sign in, open Account settings and change this password immediately. The default exists so the first sign-in is possible; it must not remain in active use.

### 12.4 Windows automatic start

The startup shortcut `RoadWatch Server.lnk` in the user's Startup folder runs `start-hidden.vbs`. That script starts the Flask server in the background and launches the combined watchdog. At the next Windows sign-in the site and hotspot return without any manual step.

### 12.5 Checking that it is running

```powershell
Invoke-WebRequest http://127.0.0.1:5000/login -UseBasicParsing
Get-Content server.log -Tail 20
Get-Content watchdog.log -Tail 20
```

A status code of 200 means the site is answering. The watchdog log records server restarts and hotspot recoveries.

## 13. Access from Phones and Other PCs

### 13.1 Addresses

| Device | Address | Notes |
| --- | --- | --- |
| This laptop | http://127.0.0.1:5000 | Always valid on the server computer |
| Phone or PC on the hotspot | http://192.168.137.1:5000 | Recommended for nearby devices |
| Device on the same external Wi-Fi | http://192.168.3.112:5000 | Address can change between networks |
| Device using the computer name | http://BHASKAR.local:5000 | May be blocked by some networks |

### 13.2 Mobile hotspot method

This is the most reliable method when the existing Wi-Fi isolates clients.

1. On the phone or other PC, open Wi-Fi settings.
2. Connect to the network named `RoadWatch`.
3. Enter the password `RoadWatch@2026`.
4. Open `http://192.168.137.1:5000` in the browser.

The laptop must stay awake and connected to its normal Wi-Fi, because the hotspot shares that internet connection. Windows may switch the hotspot off when no device is connected; the watchdog restores it within about 20 seconds.

### 13.3 Existing Wi-Fi method

Connect both devices to the same Wi-Fi and open `http://192.168.3.112:5000`. Use the current IPv4 address of the laptop, which can be checked with `Get-NetIPAddress -AddressFamily IPv4`. Shared, guest and institutional Wi-Fi networks often block communication between clients; in that case use the hotspot.

### 13.4 Firewall

A Windows Firewall rule named `RoadWatch 5000` allows inbound TCP port 5000 on all profiles. The application binds to 0.0.0.0, so it listens on every network interface. If the rule is removed, other devices cannot connect even though the site works on the laptop.

### 13.5 Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Site fails on the laptop | Server not running | Start the RoadWatch shortcut or restart Windows |
| Site works on laptop, not on phone | Hotspot is off or device on another network | Reconnect to RoadWatch and wait 30 seconds |
| Hotspot not visible | Windows turned it off | Wait 20 seconds for the watchdog |
| Address times out on external Wi-Fi | Client isolation | Use the RoadWatch hotspot |
| Browser shows HTTPS warning | Wrong scheme typed | Use http://, not https:// |
| 404 on a report | Wrong tracking number | Recheck the number from the confirmation page |
| Login rejects password | Password changed earlier | Use Forgot password or the local reset link |

## 14. Long-Term Reliability Setup

### 14.1 Start at sign-in

The Startup folder contains `RoadWatch Server.lnk`, which runs `start-hidden.vbs`. The script starts the Flask server with `HOST=0.0.0.0` and `PORT=5000`, then starts `watch-roadwatch.ps1` hidden. No console window is left open.

### 14.2 Server watchdog

`watch-roadwatch.ps1` runs continuously with a global mutex so only one copy can exist. Every 20 seconds it opens a TCP connection to port 5000 on localhost. If the connection fails, it starts the server again with the same environment and appends a line to `watchdog.log`. The log rotates when it reaches 1 MB. The watchdog was tested by stopping the server process; the site returned a 200 response again within the next check.

### 14.3 Hotspot watchdog

The same script checks the Windows tethering manager on each pass. When tethering is not On, it re-applies the RoadWatch SSID and password and starts tethering. This handles the common Windows behaviour of turning the hotspot off after a period with no connected clients.

### 14.4 Power settings

| Setting | Value |
| --- | --- |
| AC standby timeout | Never |
| AC hibernate timeout | Never |
| AC disk timeout | Never |
| AC monitor timeout | 15 minutes |
| AC lid-close action | Do nothing |
| DC standby timeout | 3 hours |
| DC monitor timeout | 3 minutes |

The laptop must remain plugged in for these AC settings to apply.

### 14.5 Log files

| File | Contents | Growth control |
| --- | --- | --- |
| server.log | HTTP requests and Flask output | Append-only; small on a local network |
| watchdog.log | Restarts, hotspot recoveries and errors | Rotated at 1 MB |
| hotspot.log | Legacy hotspot-only watchdog output | Legacy script only |

### 14.6 Recommended maintenance

- Keep the charger connected whenever the site should be available.
- Sign in to Windows after a restart; the startup entry runs at sign-in.
- Check `http://127.0.0.1:5000` once a week.
- Back up `instance/roadwatch.db` and `static/uploads/` at least monthly.
- Change the administrator password if it may have been seen by others.
- Install Windows updates at a convenient time and sign in afterwards.
- Keep the project folder name exactly `Roadwatch` so shortcuts and scripts keep working.

### 14.7 Recovery steps

1. Try the Desktop RoadWatch shortcut.
2. If it fails, open `watchdog.log` and check for repeated errors.
3. Restart Windows and sign in. The server, watchdog and hotspot start automatically.
4. If the hotspot is missing, wait 30 seconds; the watchdog checks every 20 seconds.
5. If the database is damaged, restore the most recent backup of `instance/roadwatch.db`.

## 15. Testing and Verification

The project was verified with two automated suites and a set of live checks.

| Check | Result |
| --- | --- |
| Authentication feature suite | 44 of 44 checks passed |
| Delivery and regression suite | 34 of 34 checks passed |
| In-place database migration | Passed, columns and tables created |
| Server watchdog restart test | Server stopped, watchdog restarted it, HTTP 200 returned |
| Hotspot recovery test | Hotspot switched off, watchdog restored it |
| Local access | http://127.0.0.1:5000 returned 200 |
| Hotspot access | http://192.168.137.1:5000 returned 200 |
| LAN access | http://192.168.3.112:5000 returned 200 |
| Hostname access | http://BHASKAR.local:5000 returned 200 |
| Reports counter | 0 |
| Updates counter | 0 |
| Administrator accounts | 1 |

The counters remain at zero until real reports are submitted. No test data was left in the live database.

## 16. Limitations and Future Scope

### 16.1 Current limitations

- The Flask development server is intended for small local deployments, not high-traffic public use.
- SQLite allows one writer at a time, which is ample here but not suitable for heavy concurrency.
- Traffic inside the local network uses plain HTTP.
- Google sign-in and reset email require internet access and external configuration.
- The hotspot requires a Wi-Fi adapter that supports Wi-Fi Direct and an active internet connection.
- The laptop must stay powered and signed in for the site to remain available.

### 16.2 Future enhancements

- Serve the application with Waitress or Gunicorn behind an HTTPS reverse proxy.
- Move to PostgreSQL if many administrators or high traffic are expected.
- Add rate limiting and account lockout after repeated failed sign-ins.
- Add email or SMS notifications when a report status changes.
- Add a map view, geolocation and duplicate-report detection.
- Add scheduled backups and a restore command.
- Add two-factor authentication for administrator accounts.
- Add CSV export and printable monthly reports.

## 17. Conclusion

RoadWatch provides a complete, self-contained workflow for reporting and tracking road problems. Citizens receive a clear reference number and a public status history, while the administrator gets a secure, filterable workspace and a private audit trail. The design deliberately favours simple, well-understood components: one Python file, one SQLite database, server-rendered templates and a small set of Windows scripts. Combined with automatic startup, watchdogs and power settings, this makes the system practical for long-term use on a single laptop, including access from phones and other PCs on the same network.

## 18. Source Code Listings

The complete source code follows. Generated runtime data, the SQLite database, uploaded photos, the virtual environment and secret keys are intentionally excluded. Configuration values are read from environment variables and no credentials are embedded in the source.

## 19. Complete File Listings

### File: app.py

````python
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
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please sign in to access the admin workspace.", "info")
            if request.method == "GET":
                target = request.full_path.rstrip("?")
            else:
                target = url_for("admin_dashboard")
            return redirect(url_for("login", next=target))
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
    return redirect(url_for("login"))


@app.get("/account")
@login_required
def account():
    admin = get_admin(session["admin_id"])
    if admin is None:
        session.clear()
        flash("That account no longer exists. Please sign in again.", "info")
        return redirect(url_for("login"))
    return render_template(
        "account.html",
        admin=admin,
        password_rules=[label for label, _rule in PASSWORD_RULES],
    )


@app.post("/account/email")
@login_required
def update_account_email():
    admin = get_admin(session["admin_id"])
    if admin is None:
        session.clear()
        return redirect(url_for("login"))

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
    admin = get_admin(session["admin_id"])
    if admin is None:
        session.clear()
        return redirect(url_for("login"))

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
                return redirect(url_for("login"))

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
        return redirect(url_for("login"))

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
        return redirect(url_for("login"))

    saved_state = session.pop("google_state", "")
    verifier = session.pop("google_verifier", "")
    next_url = session.pop("google_next", "") or url_for("admin_dashboard")
    if not is_safe_next_url(next_url):
        next_url = url_for("admin_dashboard")

    if request.args.get("error"):
        flash("Google sign-in was cancelled.", "info")
        return redirect(url_for("login"))

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
        return redirect(url_for("login"))

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
        return redirect(url_for("login"))

    email = (userinfo.get("email") or "").strip().lower()
    google_sub = str(userinfo.get("sub") or "").strip()
    verified = userinfo.get("email_verified") in (True, "true", "True", 1)
    if not email or not google_sub or not verified:
        flash(
            "Google did not provide a verified email address for this account.",
            "error",
        )
        return redirect(url_for("login"))

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
                return redirect(url_for("login"))
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
                    return redirect(url_for("login"))
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
            return redirect(url_for("login"))

    if admin is None:
        flash("Google sign-in could not find a matching account.", "error")
        return redirect(url_for("login"))

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
````

### File: requirements.txt

````text
Flask==3.1.2
````

### File: .gitignore

````text
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage

# Local data and generated files
instance/
static/uploads/*
!static/uploads/.gitkeep

# Environment overrides
.env
.env.*
!.env.example

# Editor and OS files
.vscode/
.idea/
.DS_Store
Thumbs.db
````

### File: start.cmd

````bat
@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment. This runs only once...
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)

for /f %%i in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } ^| Select-Object -First 1).IPAddress"') do set LANIP=%%i

set HOST=0.0.0.0
set PORT=5000

echo.
echo   RoadWatch is starting.
echo   This computer:  http://127.0.0.1:5000
if defined LANIP echo   Other devices: http://%LANIP%:5000
echo                  http://%COMPUTERNAME%.local:5000
echo.
echo   Keep this window open while using the site. Press Ctrl+C to stop.
echo.

start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"
.venv\Scripts\python.exe app.py

endlocal
````

### File: start-hidden.vbs

````vbscript
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Users\C Bhaskar\Documents\Default Project\Roadwatch"
sh.Run "cmd /c set ""HOST=0.0.0.0""&& set ""PORT=5000""&& "".venv\Scripts\python.exe"" app.py >> server.log 2>&1", 0, False
sh.Run "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""C:\Users\C Bhaskar\Documents\Default Project\Roadwatch\watch-roadwatch.ps1""", 0, False
````

### File: start-hotspot.ps1

````powershell
# Starts the RoadWatch Mobile Hotspot (SSID: RoadWatch).
# Safe to run repeatedly: it exits when the hotspot is already on.
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime]
$null = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime]

$methods = [System.WindowsRuntimeSystemExtensions].GetMethods()
$asTaskGeneric = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
$asTaskAction = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
})[0]

function Await-Result($operation, $resultType) {
    $task = $asTaskGeneric.MakeGenericMethod($resultType).Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
    return $task.Result
}

function Await-Action($operation) {
    $task = $asTaskAction.Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
}

# Wait up to 90 seconds for the normal Wi-Fi to connect after sign-in.
$profile = $null
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    $profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
    if ($profile) { break }
    Start-Sleep -Seconds 2
}

if (-not $profile) {
    Write-Output "No internet connection profile is available yet."
    exit 1
}

$manager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
$onState = [Windows.Networking.NetworkOperators.TetheringOperationalState]::On
if ($manager.TetheringOperationalState -eq $onState) {
    Write-Output "RoadWatch hotspot is already on."
    exit 0
}

$config = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration]::new()
$config.Ssid = "RoadWatch"
$config.Passphrase = "RoadWatch@2026"
Await-Action $manager.ConfigureAccessPointAsync($config)

$resultType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]
$result = Await-Result $manager.StartTetheringAsync() $resultType
Write-Output ("RoadWatch hotspot start: " + $result.Status)
if ($result.AdditionalErrorMessage) {
    Write-Output $result.AdditionalErrorMessage
}
````

### File: watch-roadwatch.ps1

````powershell
# Keeps RoadWatch available for long-term use.
# - Restarts the Flask site if port 5000 stops listening.
# - Turns the RoadWatch hotspot back on if Windows switches it off.
# Runs hidden and checks every 20 seconds.

$ErrorActionPreference = "Continue"
$project = $PSScriptRoot
$logPath = Join-Path $project "watchdog.log"

function Write-WatchdogLog {
    param([string]$Message)
    try {
        if ((Test-Path $logPath) -and ((Get-Item $logPath).Length -gt 1MB)) {
            Move-Item -LiteralPath $logPath -Destination ($logPath + ".old") -Force
        }
        Add-Content -LiteralPath $logPath -Value ("{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message)
    } catch {
        # Logging must never stop the watchdog.
    }
}

function Test-RoadWatchPort {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect("127.0.0.1", 5000, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(1200)) {
            return $false
        }
        $client.EndConnect($result)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

# Only one watchdog may run.
$mutex = New-Object System.Threading.Mutex($false, "Global\RoadWatchLongRunWatchdog")
if (-not $mutex.WaitOne(0)) {
    exit 0
}

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime]
$null = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime]

$methods = [System.WindowsRuntimeSystemExtensions].GetMethods()
$asTaskGeneric = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
$asTaskAction = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
})[0]

function Await-Result($operation, $resultType) {
    $task = $asTaskGeneric.MakeGenericMethod($resultType).Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
    return $task.Result
}

function Await-Action($operation) {
    $task = $asTaskAction.Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
}

$onState = [Windows.Networking.NetworkOperators.TetheringOperationalState]::On
$resultType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]

while ($true) {
    # 1. Keep the website listening on port 5000.
    if (-not (Test-RoadWatchPort)) {
        Write-WatchdogLog "Port 5000 is down. Starting the RoadWatch server."
        $serverCommand = 'set "HOST=0.0.0.0"&& set "PORT=5000"&& ".venv\Scripts\python.exe" app.py >> server.log 2>&1'
        Start-Process -FilePath "cmd.exe" -ArgumentList '/c', $serverCommand -WorkingDirectory $project -WindowStyle Hidden
        Start-Sleep -Seconds 4
    }

    # 2. Keep the RoadWatch hotspot available.
    try {
        $profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
        if ($profile) {
            $manager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
            if ($manager -and $manager.TetheringOperationalState -ne $onState) {
                $config = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration]::new()
                $config.Ssid = "RoadWatch"
                $config.Passphrase = "RoadWatch@2026"
                Await-Action $manager.ConfigureAccessPointAsync($config)
                $result = Await-Result $manager.StartTetheringAsync() $resultType
                Write-WatchdogLog ("Hotspot start: " + $result.Status)
            }
        }
    } catch {
        Write-WatchdogLog ("Hotspot error: " + $_.Exception.Message)
    }

    Start-Sleep -Seconds 20
}
````

### File: templates/base.html

````html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="RoadWatch helps communities report potholes, damaged roads, waterlogging, and other road safety problems.">
  <meta name="theme-color" content="#14231f">
  <title>{% block title %}RoadWatch — Report road problems{% endblock %}</title>
  <link rel="icon" href="{{ url_for('static', filename='images/roadwatch-logo.svg') }}" type="image/svg+xml">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <script src="{{ url_for('static', filename='js/app.js') }}" defer></script>
</head>
<body class="{% block body_class %}{% endblock %}">
  <a class="skip-link" href="#main-content">Skip to content</a>

  <header class="site-header">
    <div class="container nav-shell">
      <a class="brand" href="{{ url_for('index') }}" aria-label="RoadWatch home">
        <img src="{{ url_for('static', filename='images/roadwatch-logo.svg') }}" alt="" width="42" height="42">
        <span class="brand-name">Road<span>Watch</span></span>
      </a>

      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" data-nav-toggle>
        <span class="nav-toggle-label">Menu</span>
        <span class="nav-toggle-icon" aria-hidden="true"><span></span><span></span><span></span></span>
      </button>

      <nav class="site-nav" id="site-nav" aria-label="Primary navigation">
        <a href="{{ url_for('index') }}#report-form" class="{% if request.endpoint == 'index' %}is-active{% endif %}">Report an issue</a>
        <a href="{{ url_for('public_reports') }}" class="{% if request.endpoint in ('public_reports', 'report_detail', 'report_submitted') %}is-active{% endif %}">Public reports</a>
        <a href="{{ url_for('index') }}#tracker">Track a report</a>
        {% if session.get('admin_id') %}
          <a href="{{ url_for('admin_dashboard') }}" class="{% if request.endpoint == 'admin_dashboard' %}is-active{% endif %}">Admin dashboard</a>
          <div class="nav-account">
            <a class="nav-user" href="{{ url_for('account') }}" title="Account settings for {{ session.get('admin_username') }}">
              <span class="avatar avatar-sm">{{ session.get('admin_username', 'A')|initials }}</span>
              <span>{{ session.get('admin_username') }}</span>
            </a>
            <form action="{{ url_for('logout') }}" method="post">
              <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
              <button class="button button-small button-ghost" type="submit">Sign out</button>
            </form>
          </div>
        {% else %}
          <a href="{{ url_for('login') }}" class="nav-login {% if request.endpoint == 'login' %}is-active{% endif %}">Admin sign in</a>
        {% endif %}
      </nav>
    </div>
  </header>

  <main id="main-content">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="container flash-stack" role="status" aria-live="polite">
          {% for category, message in messages %}
            <div class="flash flash-{{ category }}">
              <span class="flash-marker" aria-hidden="true"></span>
              <p>{{ message }}</p>
              <button class="flash-close" type="button" aria-label="Dismiss message" data-dismiss-flash>&times;</button>
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}
  </main>

  <footer class="site-footer">
    <div class="container footer-grid">
      <div class="footer-brand">
        <div class="footer-brand-mark">
          <a class="brand brand-light" href="{{ url_for('index') }}">
            <img src="{{ url_for('static', filename='images/roadwatch-logo.svg') }}" alt="" width="38" height="38">
            <span class="brand-name">Road<span>Watch</span></span>
          </a>
        </div>
        <p>Community road reports, in one place. Built for safer journeys.</p>
      </div>
      <div class="footer-links">
        <h2>Report</h2>
        <a href="{{ url_for('index') }}#report-form">Report a road issue</a>
        <a href="{{ url_for('index') }}#tracker">Track a report</a>
      </div>
      <div class="footer-links">
        <h2>Explore</h2>
        <a href="{{ url_for('public_reports') }}">Public reports</a>
        <a href="{{ url_for('login') }}">Admin access</a>
      </div>
    </div>
    <div class="container footer-bottom">
      <p>&copy; {{ current_year }} RoadWatch. Report emergencies to local emergency services.</p>
      <p>Built with Flask &amp; SQLite.</p>
    </div>
  </footer>
</body>
</html>
````

### File: templates/index.html

````html
{% extends "base.html" %}

{% block title %}RoadWatch — Report a road problem{% endblock %}
{% block body_class %}home-page{% endblock %}

{% block content %}
  {% set selected_severity = form.get('severity') or 'Medium' %}
  <section class="hero">
    <div class="hero-road" aria-hidden="true"></div>
    <div class="container hero-grid">
      <div class="hero-copy">
        <p class="eyebrow eyebrow-light"><span class="eyebrow-dot"></span> Community road reporting</p>
        <h1>Better roads start with <span class="text-highlight">one report.</span></h1>
        <p class="hero-lead">
          Spotted a pothole, broken streetlight, or flooded street? Tell us where it is.
          Your report helps the community see what needs fixing — and gives crews a clear place to start.
        </p>
        <div class="hero-actions">
          <a class="button button-primary button-large" href="#report-form">
            Report a road issue
            <span aria-hidden="true">&rarr;</span>
          </a>
          <a class="button button-ghost button-large" href="{{ url_for('public_reports') }}">Browse reports</a>
        </div>

        <dl class="hero-stats" aria-label="RoadWatch community statistics">
          <div>
            <dt>Reports shared</dt>
            <dd>{{ stats.total }}</dd>
          </div>
          <div>
            <dt>Open reports</dt>
            <dd>{{ stats.open }}</dd>
          </div>
          <div>
            <dt>Resolved</dt>
            <dd>{{ stats.resolved }}</dd>
          </div>
          <div>
            <dt>Cities &amp; areas</dt>
            <dd>{{ stats.cities }}</dd>
          </div>
        </dl>
      </div>

      <aside class="tracker-card" id="tracker" aria-labelledby="tracker-title">
        <div class="tracker-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8">
            <circle cx="11" cy="11" r="6.5"></circle>
            <path d="m16 16 4.2 4.2"></path>
          </svg>
        </div>
        <p class="eyebrow eyebrow-dark">Already reported?</p>
        <h2 id="tracker-title">Track your report</h2>
        <p>Enter the tracking number you received when you submitted the issue.</p>
        <form class="tracker-form" action="{{ url_for('track_report') }}" method="get">
          <label for="tracking_number">Tracking number</label>
          <div class="input-button-row">
            <input id="tracking_number" name="tracking_number" type="text" placeholder="RW-20261102-ABC12" autocomplete="off" spellcheck="false" required>
            <button class="button button-primary" type="submit">Track</button>
          </div>
        </form>

        <div class="tracker-divider"></div>
        <h3>How it works</h3>
        <ol class="mini-steps">
          <li><span>1</span><p><strong>Send the details.</strong> Add the location, issue, and a photo if you can.</p></li>
          <li><span>2</span><p><strong>Get a tracking number.</strong> Use it any time to see the latest status.</p></li>
          <li><span>3</span><p><strong>Follow the progress.</strong> Updates appear on the public report timeline.</p></li>
        </ol>
      </aside>
    </div>
  </section>

  <section class="section report-section" id="report-form">
    <div class="container report-layout">
      <div class="section-intro">
        <p class="eyebrow">Report a problem</p>
        <h2>Tell us what is happening on the road.</h2>
        <p>
          Useful reports are specific. Mention the nearest landmark, the direction of travel,
          and how serious the problem feels.
        </p>
        <ul class="check-list">
          <li>One issue per report</li>
          <li>Add a clear photo when it is safe to do so</li>
          <li>Never stop in traffic or enter a closed road to take a photo</li>
        </ul>
        <div class="safety-note">
          <strong>Emergency?</strong>
          <p>If a road problem is causing immediate danger, contact your local emergency services first.</p>
        </div>
      </div>

      <form class="card form-card" action="{{ url_for('submit_report') }}" method="post" enctype="multipart/form-data">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <fieldset class="form-section">
          <legend>
            <span class="step-number">01</span>
            <span>
              <strong>Your details</strong>
              <small>We only use these to follow up on the report. They are not shown publicly.</small>
            </span>
          </legend>
          <div class="form-grid">
            <div class="field field-full">
              <label for="reporter_name">Your name <span aria-hidden="true">*</span></label>
              <input id="reporter_name" name="reporter_name" type="text" value="{{ form.get('reporter_name', '') }}" maxlength="100" autocomplete="name" required>
            </div>
            <div class="field">
              <label for="reporter_email">Email <span class="label-note">optional</span></label>
              <input id="reporter_email" name="reporter_email" type="email" value="{{ form.get('reporter_email', '') }}" maxlength="254" autocomplete="email" placeholder="you@example.com">
            </div>
            <div class="field">
              <label for="reporter_phone">Phone <span class="label-note">optional</span></label>
              <input id="reporter_phone" name="reporter_phone" type="tel" value="{{ form.get('reporter_phone', '') }}" maxlength="30" autocomplete="tel" placeholder="+91 98765 43210">
            </div>
          </div>
        </fieldset>

        <fieldset class="form-section">
          <legend>
            <span class="step-number">02</span>
            <span>
              <strong>Where is the problem?</strong>
              <small>The more precise the location, the easier it is to act on.</small>
            </span>
          </legend>
          <div class="form-grid">
            <div class="field field-full">
              <label for="road_name">Road or street name <span aria-hidden="true">*</span></label>
              <input id="road_name" name="road_name" type="text" value="{{ form.get('road_name', '') }}" maxlength="160" placeholder="e.g. MG Road, near the metro station" required>
            </div>
            <div class="field">
              <label for="location">Nearest landmark or address <span aria-hidden="true">*</span></label>
              <input id="location" name="location" type="text" value="{{ form.get('location', '') }}" maxlength="200" placeholder="e.g. Opposite City Mall" required>
            </div>
            <div class="field">
              <label for="city">City or area <span aria-hidden="true">*</span></label>
              <input id="city" name="city" type="text" value="{{ form.get('city', '') }}" maxlength="100" placeholder="e.g. Bengaluru" required>
            </div>
          </div>
        </fieldset>

        <fieldset class="form-section">
          <legend>
            <span class="step-number">03</span>
            <span>
              <strong>What did you find?</strong>
              <small>Choose the closest match and tell us what you saw.</small>
            </span>
          </legend>
          <div class="form-grid">
            <div class="field field-full">
              <label for="issue_type">Issue type <span aria-hidden="true">*</span></label>
              <select id="issue_type" name="issue_type" required>
                <option value="" {% if not form.get('issue_type') %}selected{% endif %} disabled>Select an issue type</option>
                {% for issue in issue_types %}
                  <option value="{{ issue }}" {% if form.get('issue_type') == issue %}selected{% endif %}>{{ issue }}</option>
                {% endfor %}
              </select>
            </div>

            <fieldset class="field field-full severity-field">
              <legend>How serious is it? <span aria-hidden="true">*</span></legend>
              <div class="severity-grid">
                {% for severity in severities %}
                  <label class="severity-card severity-{{ severity|lower }}">
                    <input type="radio" name="severity" value="{{ severity }}" {% if selected_severity == severity %}checked{% endif %} required>
                    <span class="severity-dot" aria-hidden="true"></span>
                    <span class="severity-copy">
                      <strong>{{ severity }}</strong>
                      <small>{{ severity_help[severity] }}</small>
                    </span>
                  </label>
                {% endfor %}
              </div>
            </fieldset>

            <div class="field field-full">
              <div class="label-row">
                <label for="description">Description <span aria-hidden="true">*</span></label>
                <span class="label-note" data-description-count>0 / 3000</span>
              </div>
              <textarea id="description" name="description" rows="5" maxlength="3000" minlength="10" placeholder="Describe the size, position, and any risk it creates. For example: a deep pothole in the left lane just after the junction." required>{{ form.get('description', '') }}</textarea>
            </div>

            <div class="field field-full">
              <span class="field-label" id="photo-label">Photo <span class="label-note">optional</span></span>
              <label class="file-drop" for="photo">
                <input id="photo" name="photo" type="file" accept="image/jpeg,image/png,image/gif,image/webp" data-file-input aria-labelledby="photo-label">
                <span class="file-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <rect x="3" y="4" width="18" height="16" rx="3"></rect>
                    <circle cx="9" cy="9" r="1.6"></circle>
                    <path d="m4 17 5-5 4 4 2-2 5 5"></path>
                  </svg>
                </span>
                <span class="file-copy">
                  <strong>Choose a photo</strong>
                  <small>JPG, PNG, GIF, or WebP · up to 8 MB</small>
                  <span class="file-name" data-file-name>No photo selected</span>
                </span>
              </label>
            </div>
          </div>
        </fieldset>

        <div class="form-footer">
          <p>By submitting, you confirm this report is accurate and may be shown publicly. Your contact details stay private.</p>
          <button class="button button-primary button-large" type="submit">
            Submit report
            <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      </form>
    </div>
  </section>

  {% if recent %}
    <section class="section recent-section">
      <div class="container">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Community activity</p>
            <h2>Latest reports</h2>
          </div>
          <a class="text-link" href="{{ url_for('public_reports') }}">View all reports <span aria-hidden="true">&rarr;</span></a>
        </div>
        <div class="report-grid">
          {% for report in recent %}
            <article class="report-card">
              <a class="report-card-media" href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}" aria-label="View report: {{ report['road_name'] }}, {{ report['status'] }} status">
                {% if report['photo_filename'] %}
                  <img src="{{ url_for('static', filename='uploads/' ~ report['photo_filename']) }}" alt="Photo of {{ report['issue_type']|lower }} on {{ report['road_name'] }}" loading="lazy">
                {% else %}
                  <span class="report-card-placeholder" aria-hidden="true">
                    <svg viewBox="0 0 64 64" width="48" height="48" fill="none" stroke="currentColor" stroke-width="3">
                      <path d="M25 53 30 11h4l5 42"></path>
                      <path d="M31 40h2M32 29h1"></path>
                    </svg>
                  </span>
                {% endif %}
                <span class="status-badge status-{{ report['status']|status_slug }}">{{ report['status'] }}</span>
              </a>
              <div class="report-card-body">
                <div class="report-card-meta">
                  <span>{{ report['issue_type'] }}</span>
                  <span>{{ report['created_at']|readable_datetime }}</span>
                </div>
                <h3><a href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}">{{ report['road_name'] }}</a></h3>
                <p class="report-location">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"></path>
                    <circle cx="12" cy="10" r="2.5"></circle>
                  </svg>
                  {{ report['location'] }}{% if report['city'] %}, {{ report['city'] }}{% endif %}
                </p>
              </div>
            </article>
          {% endfor %}
        </div>
      </div>
    </section>
  {% endif %}
{% endblock %}
````

### File: templates/submitted.html

````html
{% extends "base.html" %}

{% block title %}Report received — RoadWatch{% endblock %}
{% block body_class %}confirmation-page{% endblock %}

{% block content %}
  <section class="section confirmation-section">
    <div class="container narrow">
      <div class="card confirmation-card">
        <div class="success-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="m5 12 4.5 4.5L19 7"></path>
          </svg>
        </div>
        <p class="eyebrow">Report received</p>
        <h1>Thank you, {{ report['reporter_name'].split()[0] }}.</h1>
        <p class="confirmation-lead">
          Your report is in the review queue. Keep the tracking number below — it is the
          fastest way to check for updates.
        </p>

        <div class="tracking-box">
          <div>
            <span>Your tracking number</span>
            <strong>{{ report['tracking_number'] }}</strong>
          </div>
          <button class="button button-primary" type="button" data-copy="{{ report['tracking_number'] }}">Copy</button>
        </div>
        <p class="tracking-warning">Save this number somewhere safe. You will need it to find your report again.</p>

        <div class="confirmation-summary">
          <div>
            <span>Road</span>
            <strong>{{ report['road_name'] }}</strong>
          </div>
          <div>
            <span>Location</span>
            <strong>{{ report['location'] }}, {{ report['city'] }}</strong>
          </div>
          <div>
            <span>Issue</span>
            <strong>{{ report['issue_type'] }}</strong>
          </div>
          <div>
            <span>Current status</span>
            <strong><span class="status-badge status-{{ report['status']|status_slug }}">{{ report['status'] }}</span></strong>
          </div>
        </div>

        <div class="confirmation-actions">
          <a class="button button-primary" href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}">View your report</a>
          <a class="button button-ghost" href="{{ url_for('index') }}#report-form">Report another issue</a>
          <a class="text-link" href="{{ url_for('public_reports') }}">Browse public reports</a>
        </div>
      </div>

      <div class="next-steps">
        <h2>What happens next?</h2>
        <ol class="next-steps-list">
          <li>
            <span class="next-step-number">1</span>
            <p><strong>Review.</strong> An administrator checks the report and confirms the details.</p>
          </li>
          <li>
            <span class="next-step-number">2</span>
            <p><strong>Update.</strong> The status changes as the issue moves toward a fix.</p>
          </li>
          <li>
            <span class="next-step-number">3</span>
            <p><strong>Follow along.</strong> Reopen the report with your tracking number at any time.</p>
          </li>
        </ol>
      </div>
    </div>
  </section>
{% endblock %}
````

### File: templates/reports.html

````html
{% extends "base.html" %}

{% block title %}Public reports — RoadWatch{% endblock %}
{% block body_class %}reports-page{% endblock %}

{% block content %}
  <section class="page-hero">
    <div class="container page-hero-inner">
      <div>
        <p class="eyebrow">Community map of needs</p>
        <h1>Public road reports</h1>
        <p>Browse the issues residents have shared. Search by street, area, or tracking number.</p>
      </div>
      <a class="button button-primary" href="{{ url_for('index') }}#report-form">Report an issue <span aria-hidden="true">&rarr;</span></a>
    </div>
  </section>

  <section class="section section-tight">
    <div class="container">
      <form class="filters-card" action="{{ url_for('public_reports') }}" method="get" role="search">
        <div class="field filter-search">
          <label for="q">Search reports</label>
          <div class="input-with-icon">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <circle cx="11" cy="11" r="6.5"></circle>
              <path d="m16 16 4.2 4.2"></path>
            </svg>
            <input id="q" name="q" type="search" value="{{ filters.q }}" placeholder="Street, landmark, city, or tracking number" maxlength="100">
          </div>
        </div>
        <div class="field">
          <label for="status">Status</label>
          <select id="status" name="status">
            <option value="">All statuses</option>
            {% for status in public_statuses %}
              <option value="{{ status }}" {% if filters.status == status %}selected{% endif %}>{{ status }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <label for="issue_type">Issue type</label>
          <select id="issue_type" name="issue_type">
            <option value="">All issues</option>
            {% for issue in issue_types %}
              <option value="{{ issue }}" {% if filters.issue_type == issue %}selected{% endif %}>{{ issue }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <label for="severity">Severity</label>
          <select id="severity" name="severity">
            <option value="">All levels</option>
            {% for severity in severities %}
              <option value="{{ severity }}" {% if filters.severity == severity %}selected{% endif %}>{{ severity }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="filter-actions">
          <button class="button button-primary" type="submit">Apply filters</button>
          {% if has_filters %}
            <a class="button button-ghost" href="{{ url_for('public_reports') }}">Clear</a>
          {% endif %}
        </div>
      </form>

      <div class="results-bar">
        <p>
          {% if pagination.total %}
            Showing <strong>{{ pagination.start }}–{{ pagination.end }}</strong> of
            <strong>{{ pagination.total }}</strong> report{% if pagination.total != 1 %}s{% endif %}
          {% else %}
            No reports found
          {% endif %}
        </p>
        {% if filters.q %}
          <p class="results-query">Search: “{{ filters.q }}”</p>
        {% endif %}
      </div>

      {% if reports %}
        <div class="report-grid report-grid-wide">
          {% for report in reports %}
            <article class="report-card">
              <a class="report-card-media" href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}" aria-label="View report: {{ report['road_name'] }}, {{ report['status'] }} status, {{ report['severity'] }} severity">
                {% if report['photo_filename'] %}
                  <img src="{{ url_for('static', filename='uploads/' ~ report['photo_filename']) }}" alt="Photo of {{ report['issue_type']|lower }} on {{ report['road_name'] }}" loading="lazy">
                {% else %}
                  <span class="report-card-placeholder" aria-hidden="true">
                    <svg viewBox="0 0 64 64" width="48" height="48" fill="none" stroke="currentColor" stroke-width="3">
                      <path d="M25 53 30 11h4l5 42"></path>
                      <path d="M31 40h2M32 29h1"></path>
                    </svg>
                  </span>
                {% endif %}
                <span class="status-badge status-{{ report['status']|status_slug }}">{{ report['status'] }}</span>
                <span class="severity-pill severity-pill-{{ report['severity']|lower }}">{{ report['severity'] }}</span>
              </a>
              <div class="report-card-body">
                <div class="report-card-meta">
                  <span>{{ report['issue_type'] }}</span>
                  <span>{{ report['created_at']|readable_datetime }}</span>
                </div>
                <h2><a href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}">{{ report['road_name'] }}</a></h2>
                <p class="report-location">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"></path>
                    <circle cx="12" cy="10" r="2.5"></circle>
                  </svg>
                  {{ report['location'] }}, {{ report['city'] }}
                </p>
                <div class="report-card-footer">
                  <span class="tracking-mini">{{ report['tracking_number'] }}</span>
                  <a class="text-link" href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}">View <span aria-hidden="true">&rarr;</span></a>
                </div>
              </div>
            </article>
          {% endfor %}
        </div>

        {% if pagination.pages > 1 %}
          <nav class="pagination" aria-label="Report pages">
            {% if pagination.has_prev %}
              <a class="pagination-link" href="{{ url_for('public_reports', page=pagination.prev_page, q=filters.q, status=filters.status, issue_type=filters.issue_type, severity=filters.severity) }}">&larr; Previous</a>
            {% else %}
              <span class="pagination-link is-disabled">&larr; Previous</span>
            {% endif %}
            <span class="pagination-status">Page {{ pagination.page }} of {{ pagination.pages }}</span>
            {% if pagination.has_next %}
              <a class="pagination-link" href="{{ url_for('public_reports', page=pagination.next_page, q=filters.q, status=filters.status, issue_type=filters.issue_type, severity=filters.severity) }}">Next &rarr;</a>
            {% else %}
              <span class="pagination-link is-disabled">Next &rarr;</span>
            {% endif %}
          </nav>
        {% endif %}
      {% else %}
        <div class="empty-state">
          <div class="empty-icon" aria-hidden="true">
            <svg viewBox="0 0 64 64" width="54" height="54" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M25 53 30 11h4l5 42"></path>
              <path d="M31 40h2M32 29h1"></path>
            </svg>
          </div>
          <h2>No reports match those filters</h2>
          <p>Try a broader search or clear the filters to see all public reports.</p>
          {% if has_filters %}
            <a class="button button-primary" href="{{ url_for('public_reports') }}">Clear filters</a>
          {% else %}
            <a class="button button-primary" href="{{ url_for('index') }}#report-form">Be the first to report</a>
          {% endif %}
        </div>
      {% endif %}
    </div>
  </section>
{% endblock %}
````

### File: templates/report_detail.html

````html
{% extends "base.html" %}

{% block title %}{{ report['road_name'] }} — RoadWatch{% endblock %}
{% block body_class %}report-detail-page{% endblock %}

{% block content %}
  <section class="detail-hero">
    <div class="container">
      <a class="back-link" href="{{ url_for('public_reports') }}"><span aria-hidden="true">&larr;</span> All public reports</a>
      <div class="detail-heading">
        <div>
          <div class="detail-kicker">
            <span class="status-badge status-{{ report['status']|status_slug }}">{{ report['status'] }}</span>
            <span class="severity-pill severity-pill-{{ report['severity']|lower }}">{{ report['severity'] }} severity</span>
            <span class="issue-label">{{ report['issue_type'] }}</span>
          </div>
          <h1>{{ report['road_name'] }}</h1>
          <p class="detail-location">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"></path>
              <circle cx="12" cy="10" r="2.5"></circle>
            </svg>
            {{ report['location'] }}, {{ report['city'] }}
          </p>
        </div>
        <div class="detail-tracking">
          <span>Tracking number</span>
          <strong>{{ report['tracking_number'] }}</strong>
          <button class="button button-small button-ghost" type="button" data-copy="{{ report['tracking_number'] }}">Copy</button>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container detail-layout">
      <div class="detail-main">
        {% if report['photo_filename'] %}
          <figure class="detail-photo">
            <img src="{{ url_for('static', filename='uploads/' ~ report['photo_filename']) }}" alt="Photo of {{ report['issue_type']|lower }} on {{ report['road_name'] }}">
          </figure>
        {% endif %}

        <article class="card detail-card">
          <h2>About this report</h2>
          <p class="description-text">{{ report['description'] }}</p>

          <dl class="detail-facts">
            <div>
              <dt>Issue</dt>
              <dd>{{ report['issue_type'] }}</dd>
            </div>
            <div>
              <dt>Severity</dt>
              <dd><span class="severity-text severity-text-{{ report['severity']|lower }}">{{ report['severity'] }}</span></dd>
            </div>
            <div>
              <dt>Reported</dt>
              <dd>{{ report['created_at']|readable_datetime }}</dd>
            </div>
            <div>
              <dt>Last updated</dt>
              <dd>{{ report['updated_at']|readable_datetime }}</dd>
            </div>
          </dl>

          <div class="detail-actions">
            <a class="button button-ghost" href="{{ maps_url }}" target="_blank" rel="noopener noreferrer">
              Open location in Maps
              <span aria-hidden="true">&nearr;</span>
            </a>
            <a class="button button-ghost" href="{{ url_for('index') }}#tracker">Track another report</a>
          </div>
        </article>
      </div>

      <div class="detail-sidebar">
        <div class="card status-card">
          <p class="eyebrow">Current status</p>
          <div class="current-status status-panel-{{ report['status']|status_slug }}">
            <span class="status-pulse" aria-hidden="true"></span>
            <strong>{{ report['status'] }}</strong>
          </div>
          <p class="status-help">
            {% if report['status'] == 'Submitted' %}
              The report has been received and is waiting for review.
            {% elif report['status'] == 'Under Review' %}
              A reviewer is checking the details and location.
            {% elif report['status'] == 'In Progress' %}
              The issue has been accepted and work is underway.
            {% elif report['status'] == 'Resolved' %}
              The issue has been marked as resolved.
            {% else %}
              This report is not currently active.
            {% endif %}
          </p>

          <div class="timeline-wrap">
            <h2>Updates</h2>
            <ol class="timeline">
              {% for update in updates %}
                <li class="timeline-item">
                  <span class="timeline-dot timeline-dot-{{ update['status']|status_slug }}" aria-hidden="true"></span>
                  <div class="timeline-content">
                    <div class="timeline-head">
                      <strong>{{ update['status'] }}</strong>
                      <time datetime="{{ update['created_at'] }}">{{ update['created_at']|readable_datetime }}</time>
                    </div>
                    {% if update['note'] %}
                      <p>{{ update['note'] }}</p>
                    {% endif %}
                    {% if update['admin_username'] %}
                      <span class="timeline-author">RoadWatch team</span>
                    {% endif %}
                  </div>
                </li>
              {% endfor %}
            </ol>
          </div>
        </div>

        <div class="help-card">
          <h2>Spotted something else?</h2>
          <p>Submit a separate report so each location can be tracked clearly.</p>
          <a class="text-link" href="{{ url_for('index') }}#report-form">Report another issue <span aria-hidden="true">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
{% endblock %}
````

### File: templates/login.html

````html
{% extends "base.html" %}

{% block title %}Admin sign in — RoadWatch{% endblock %}
{% block body_class %}login-page{% endblock %}

{% block content %}
  <section class="auth-section">
    <div class="auth-backdrop" aria-hidden="true"></div>
    <div class="container auth-shell">
      <div class="auth-intro">
        <p class="eyebrow eyebrow-light">RoadWatch workspace</p>
        <h1>Keep the reports moving.</h1>
        <p>Sign in to review incoming issues, add public updates, and keep residents informed from first report to resolution.</p>
        <ul class="auth-points">
          <li>Review the report queue</li>
          <li>Update public status timelines</li>
          <li>Keep private follow-up notes</li>
        </ul>
      </div>

      <div class="card auth-card">
        <div class="auth-mark" aria-hidden="true">
          <img src="{{ url_for('static', filename='images/roadwatch-logo.svg') }}" alt="" width="48" height="48">
        </div>
        <h2>Admin sign in</h2>
        <p class="auth-subtitle">Use your RoadWatch administrator account.</p>

        <form action="{{ url_for('login') }}" method="post">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="hidden" name="next" value="{{ next_url }}">

          <div class="field">
            <label for="username">Username</label>
            <input id="username" name="username" type="text" autocomplete="username" maxlength="100" required autofocus>
          </div>
          <div class="field">
            <div class="label-row">
              <label for="password">Password</label>
              <a class="text-link auth-inline-link" href="{{ url_for('forgot_password') }}">Forgot password?</a>
            </div>
            <input id="password" name="password" type="password" autocomplete="current-password" required>
          </div>

          <button class="button button-primary button-full" type="submit">Sign in</button>
        </form>

        <div class="auth-divider" role="separator" aria-label="or"><span>or</span></div>

        <a class="button button-google button-full" href="{{ url_for('google_login', next=next_url) }}">
          <svg class="google-icon" viewBox="0 0 48 48" width="18" height="18" aria-hidden="true" focusable="false">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
          </svg>
          Continue with Google
        </a>

        {% if not google_signin_enabled %}
          <p class="auth-fineprint">Google sign-in needs a one-time Google Cloud setup by the site owner.</p>
        {% endif %}

        <p class="auth-help">Need access? Contact the person who manages this RoadWatch installation.</p>
        <a class="text-link auth-home-link" href="{{ url_for('index') }}"><span aria-hidden="true">&larr;</span> Back to RoadWatch</a>
      </div>
    </div>
  </section>
{% endblock %}
````

### File: templates/account.html

````html
{% extends "base.html" %}

{% block title %}Account settings — RoadWatch{% endblock %}
{% block body_class %}account-page{% endblock %}

{% block content %}
  <section class="section section-tight account-section">
    <div class="container account-shell">
      <div class="account-heading">
        <p class="eyebrow">Admin account</p>
        <h1>Account settings</h1>
        <p>Manage your contact email, choose a strong password, and connect Google sign-in.</p>
      </div>

      <div class="account-grid">
        <section class="card account-card" aria-labelledby="profile-heading">
          <h2 id="profile-heading">Profile</h2>
          <p class="account-subtitle">Your username is used to sign in and cannot be changed here.</p>

          <dl class="account-meta">
            <div>
              <dt>Username</dt>
              <dd>{{ admin.username }}</dd>
            </div>
            <div>
              <dt>Google sign-in</dt>
              <dd>{% if admin.google_sub %}Connected{% else %}Not connected{% endif %}</dd>
            </div>
          </dl>

          <form action="{{ url_for('update_account_email') }}" method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div class="field">
              <label for="email">Contact email</label>
              <input id="email" name="email" type="email" value="{{ admin.email or '' }}" autocomplete="email" maxlength="254" placeholder="name@example.com">
              <p class="field-help">Used for password reset links and to match your Google account.</p>
            </div>
            <button class="button button-primary" type="submit">Save email</button>
          </form>
        </section>

        <section class="card account-card" aria-labelledby="password-heading">
          <h2 id="password-heading">Change password</h2>
          <p class="account-subtitle">Enter your current password, then choose a new one and re-enter it.</p>

          <form action="{{ url_for('update_account_password') }}" method="post" data-password-form>
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div class="field">
              <label for="current_password">Current password</label>
              <input id="current_password" name="current_password" type="password" autocomplete="current-password" required>
            </div>

            <div class="field">
              <label for="new_password">New strong password</label>
              <input id="new_password" name="new_password" type="password" autocomplete="new-password" minlength="12" required data-password-input>
              <div class="password-meter" aria-hidden="true"><span data-password-meter></span></div>
              <ul class="password-rules" data-password-rules>
                {% for rule in password_rules %}
                  <li>{{ rule }}</li>
                {% endfor %}
              </ul>
            </div>

            <div class="field">
              <label for="confirm_password">Re-enter new password</label>
              <input id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" minlength="12" required data-password-confirm>
              <p class="field-feedback" data-password-match hidden>Passwords do not match yet.</p>
            </div>

            <button class="button button-primary" type="submit">Update password</button>
          </form>
        </section>
      </div>

      <section class="card account-card account-card-wide" aria-labelledby="google-heading">
        <h2 id="google-heading">Google sign-in</h2>
        {% if admin.google_sub %}
          <p>This account is linked to Google. You can sign in with the Google button on the sign-in page or keep using your username and password.</p>
        {% elif google_signin_enabled %}
          <p>Google sign-in is available. Save the same email address you use for Google, sign out, then choose <strong>Continue with Google</strong> to link the account.</p>
        {% else %}
          <p>Google sign-in is not configured yet. The site owner can enable it with these environment variables:</p>
          <ul class="account-setup">
            <li><code>GOOGLE_CLIENT_ID</code> — from Google Cloud Console</li>
            <li><code>GOOGLE_CLIENT_SECRET</code> — from Google Cloud Console</li>
            <li><code>ROADWATCH_GOOGLE_ALLOWED_EMAILS</code> — optional comma-separated list of emails allowed to create an account</li>
          </ul>
          <p class="account-note">Add <code>{{ url_for('google_callback', _external=True) }}</code> as an authorized redirect URI in the Google Cloud OAuth client.</p>
        {% endif %}
      </section>

      <p class="account-back"><a class="text-link" href="{{ url_for('admin_dashboard') }}"><span aria-hidden="true">&larr;</span> Back to the report queue</a></p>
    </div>
  </section>
{% endblock %}
````

### File: templates/forgot_password.html

````html
{% extends "base.html" %}

{% block title %}Forgot password — RoadWatch{% endblock %}
{% block body_class %}login-page{% endblock %}

{% block content %}
  <section class="auth-section">
    <div class="auth-backdrop" aria-hidden="true"></div>
    <div class="container auth-shell">
      <div class="auth-intro">
        <p class="eyebrow eyebrow-light">Account recovery</p>
        <h1>Get back to the queue.</h1>
        <p>Enter your RoadWatch username or the email saved on your account. We will prepare a one-time link to choose a new password.</p>
        <ul class="auth-points">
          <li>The link expires after 30 minutes</li>
          <li>Each link works only once</li>
          <li>Your current password stays active until you finish</li>
        </ul>
      </div>

      <div class="card auth-card">
        <div class="auth-mark" aria-hidden="true">
          <img src="{{ url_for('static', filename='images/roadwatch-logo.svg') }}" alt="" width="48" height="48">
        </div>

        {% if not submitted %}
          <h2>Forgot password</h2>
          <p class="auth-subtitle">Enter the username or email address for your admin account.</p>

          <form action="{{ url_for('forgot_password') }}" method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div class="field">
              <label for="identifier">Username or email</label>
              <input id="identifier" name="identifier" type="text" autocomplete="username" maxlength="254" required autofocus>
            </div>
            <button class="button button-primary button-full" type="submit">Send reset link</button>
          </form>
        {% else %}
          <h2>Reset instructions</h2>
          {% if delivered %}
            <p class="auth-subtitle">If that account exists and has an email address, a reset link has been sent. Check the inbox and spam folder.</p>
          {% elif reset_link %}
            <p class="auth-subtitle">Email delivery is not configured, so the one-time link is shown here. It only appears on the RoadWatch server computer.</p>
            <div class="reset-link-box">
              <label for="reset_link">One-time reset link</label>
              <input id="reset_link" type="text" value="{{ reset_link }}" readonly>
              <div class="reset-link-actions">
                <a class="button button-primary button-small" href="{{ reset_link }}">Open reset page</a>
                <button class="button button-ghost button-small" type="button" data-copy="{{ reset_link }}">Copy link</button>
              </div>
            </div>
            <p class="auth-fineprint">This link expires in 30 minutes and works once.</p>
          {% else %}
            <p class="auth-subtitle">If that account exists, reset instructions have been prepared. Check the email saved on the account. If email is not set up, ask the site owner to reset the password from the RoadWatch server.</p>
          {% endif %}
        {% endif %}

        <p class="auth-help"><a class="text-link" href="{{ url_for('login') }}">Back to sign in</a></p>
      </div>
    </div>
  </section>
{% endblock %}
````

### File: templates/reset_password.html

````html
{% extends "base.html" %}

{% block title %}Reset password — RoadWatch{% endblock %}
{% block body_class %}login-page{% endblock %}

{% block content %}
  <section class="auth-section">
    <div class="auth-backdrop" aria-hidden="true"></div>
    <div class="container auth-shell">
      <div class="auth-intro">
        <p class="eyebrow eyebrow-light">Account recovery</p>
        <h1>Choose a stronger password.</h1>
        <p>Use at least 12 characters with uppercase and lowercase letters, a number, and a symbol. Do not reuse your username or site name.</p>
        <ul class="auth-points">
          <li>Your new password is hashed before storage</li>
          <li>The reset link stops working after one use</li>
          <li>Sign in again with the new password</li>
        </ul>
      </div>

      <div class="card auth-card">
        <div class="auth-mark" aria-hidden="true">
          <img src="{{ url_for('static', filename='images/roadwatch-logo.svg') }}" alt="" width="48" height="48">
        </div>

        {% if valid %}
          <h2>New password</h2>
          <p class="auth-subtitle">Setting a new password for <strong>{{ username }}</strong>.</p>

          <form action="{{ url_for('reset_password', token=token) }}" method="post" data-password-form>
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

            <div class="field">
              <label for="new_password">New strong password</label>
              <input id="new_password" name="new_password" type="password" autocomplete="new-password" minlength="12" required autofocus data-password-input>
              <div class="password-meter" aria-hidden="true"><span data-password-meter></span></div>
              <ul class="password-rules" data-password-rules>
                <li>At least 12 characters</li>
                <li>An uppercase letter (A-Z)</li>
                <li>A lowercase letter (a-z)</li>
                <li>A number (0-9)</li>
                <li>A symbol such as ! ? @ # $ %</li>
              </ul>
            </div>

            <div class="field">
              <label for="confirm_password">Re-enter new password</label>
              <input id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" minlength="12" required data-password-confirm>
              <p class="field-feedback" data-password-match hidden>Passwords do not match yet.</p>
            </div>

            <button class="button button-primary button-full" type="submit">Set new password</button>
          </form>
        {% else %}
          <h2>This link has expired</h2>
          <p class="auth-subtitle">The reset link is invalid, has already been used, or has expired. Request a fresh link to continue.</p>
          <a class="button button-primary button-full" href="{{ url_for('forgot_password') }}">Request a new link</a>
        {% endif %}

        <p class="auth-help"><a class="text-link" href="{{ url_for('login') }}">Back to sign in</a></p>
      </div>
    </div>
  </section>
{% endblock %}
````

### File: templates/error.html

````html
{% extends "base.html" %}

{% block title %}{{ error_title }} — RoadWatch{% endblock %}

{% block content %}
  <section class="section error-section">
    <div class="container narrow">
      <div class="card error-card">
        <span class="error-code">{{ status_code }}</span>
        <p class="eyebrow">RoadWatch</p>
        <h1>{{ error_title }}</h1>
        <p>{{ error_message }}</p>
        <div class="error-actions">
          <a class="button button-primary" href="{{ url_for('index') }}">Back to home</a>
          <a class="button button-ghost" href="{{ url_for('public_reports') }}">Browse public reports</a>
        </div>
      </div>
    </div>
  </section>
{% endblock %}
````

### File: templates/admin/dashboard.html

````html
{% extends "base.html" %}

{% block title %}Admin dashboard — RoadWatch{% endblock %}
{% block body_class %}admin-page{% endblock %}

{% block content %}
  <section class="dashboard-hero">
    <div class="container">
      <div class="dashboard-heading">
        <div>
          <p class="eyebrow eyebrow-light">Admin workspace</p>
          <h1>Report queue</h1>
          <p>Review incoming issues, keep the public timeline current, and record internal follow-up.</p>
        </div>
        <div class="dashboard-user">
          <span class="avatar">{{ session.get('admin_username', 'A')|initials }}</span>
          <div>
            <span>Signed in as</span>
            <strong>{{ session.get('admin_username') }}</strong>
          </div>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card">
          <span class="stat-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M5 4h14v16H5z"></path>
              <path d="M8 8h8M8 12h8M8 16h5"></path>
            </svg>
          </span>
          <div><span>Total reports</span><strong>{{ stats.total }}</strong></div>
        </div>
        <div class="stat-card">
          <span class="stat-icon stat-icon-amber" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.8">
              <circle cx="12" cy="12" r="8.5"></circle>
              <path d="M12 7v5l3 2"></path>
            </svg>
          </span>
          <div><span>Open reports</span><strong>{{ stats.open }}</strong></div>
        </div>
        <div class="stat-card">
          <span class="stat-icon stat-icon-red" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M12 3 2.8 20h18.4L12 3Z"></path>
              <path d="M12 9v4M12 16.5v.2"></path>
            </svg>
          </span>
          <div><span>High priority</span><strong>{{ stats.urgent }}</strong></div>
        </div>
        <div class="stat-card">
          <span class="stat-icon stat-icon-green" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.8">
              <circle cx="12" cy="12" r="8.5"></circle>
              <path d="m8 12 2.5 2.5L16.5 8"></path>
            </svg>
          </span>
          <div><span>Resolved</span><strong>{{ stats.resolved }}</strong></div>
        </div>
      </div>
    </div>
  </section>

  <section class="section section-tight">
    <div class="container">
      <form class="filters-card admin-filters" action="{{ url_for('admin_dashboard') }}" method="get" role="search">
        <div class="field filter-search">
          <label for="q">Search the queue</label>
          <div class="input-with-icon">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <circle cx="11" cy="11" r="6.5"></circle>
              <path d="m16 16 4.2 4.2"></path>
            </svg>
            <input id="q" name="q" type="search" value="{{ filters.q }}" placeholder="Tracking number, reporter, street, or city" maxlength="100">
          </div>
        </div>
        <div class="field">
          <label for="status">Status</label>
          <select id="status" name="status">
            <option value="">All statuses</option>
            {% for status in statuses %}
              <option value="{{ status }}" {% if filters.status == status %}selected{% endif %}>{{ status }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <label for="issue_type">Issue type</label>
          <select id="issue_type" name="issue_type">
            <option value="">All issues</option>
            {% for issue in issue_types %}
              <option value="{{ issue }}" {% if filters.issue_type == issue %}selected{% endif %}>{{ issue }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <label for="severity">Severity</label>
          <select id="severity" name="severity">
            <option value="">All levels</option>
            {% for severity in severities %}
              <option value="{{ severity }}" {% if filters.severity == severity %}selected{% endif %}>{{ severity }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="filter-actions">
          <button class="button button-primary" type="submit">Apply filters</button>
          {% if has_filters %}
            <a class="button button-ghost" href="{{ url_for('admin_dashboard') }}">Clear</a>
          {% endif %}
        </div>
      </form>

      <div class="results-bar">
        <p>
          {% if pagination.total %}
            Showing <strong>{{ pagination.start }}–{{ pagination.end }}</strong> of
            <strong>{{ pagination.total }}</strong> report{% if pagination.total != 1 %}s{% endif %}
          {% else %}
            No reports found
          {% endif %}
        </p>
        <a class="text-link" href="{{ url_for('public_reports') }}">Open public view <span aria-hidden="true">&nearr;</span></a>
      </div>

      {% if reports %}
        <div class="admin-list">
          {% for report in reports %}
            <article class="admin-report">
              <div class="admin-report-top">
                <div class="admin-thumb">
                  {% if report['photo_filename'] %}
                    <img src="{{ url_for('static', filename='uploads/' ~ report['photo_filename']) }}" alt="Photo of {{ report['issue_type']|lower }} on {{ report['road_name'] }}" loading="lazy">
                  {% else %}
                    <span aria-hidden="true">
                      <svg viewBox="0 0 64 64" width="32" height="32" fill="none" stroke="currentColor" stroke-width="3">
                        <path d="M25 53 30 11h4l5 42"></path>
                        <path d="M31 40h2M32 29h1"></path>
                      </svg>
                    </span>
                  {% endif %}
                </div>

                <div class="admin-report-copy">
                  <div class="admin-report-kicker">
                    <span class="status-badge status-{{ report['status']|status_slug }}">{{ report['status'] }}</span>
                    <span class="severity-pill severity-pill-{{ report['severity']|lower }}">{{ report['severity'] }}</span>
                    <span class="tracking-mini">{{ report['tracking_number'] }}</span>
                  </div>
                  <h2><a href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}">{{ report['road_name'] }}</a></h2>
                  <p class="admin-location">{{ report['location'] }}, {{ report['city'] }} · {{ report['issue_type'] }}</p>
                  <p class="admin-description">{{ report['description'] }}</p>
                  <div class="admin-meta">
                    <span><strong>Reported</strong> {{ report['created_at']|readable_datetime }}</span>
                    <span><strong>By</strong> {{ report['reporter_name'] }}</span>
                    {% if report['reporter_email'] %}
                      <span><strong>Email</strong> <a href="mailto:{{ report['reporter_email'] }}">{{ report['reporter_email'] }}</a></span>
                    {% endif %}
                    {% if report['reporter_phone'] %}
                      <span><strong>Phone</strong> <a href="tel:{{ report['reporter_phone'] }}">{{ report['reporter_phone'] }}</a></span>
                    {% endif %}
                  </div>
                  {% if report['admin_note'] %}
                    <p class="internal-note"><strong>Internal note:</strong> {{ report['admin_note'] }}</p>
                  {% endif %}
                </div>

                <div class="admin-report-links">
                  <a class="button button-small button-ghost" href="{{ url_for('report_detail', tracking_number=report['tracking_number']) }}">Public page</a>
                </div>
              </div>

              <details class="admin-update">
                <summary>
                  <span>Review and update</span>
                  <span class="summary-hint">Change status, add a public update, or save a private note</span>
                </summary>
                <form action="{{ url_for('admin_update_report', report_id=report['id']) }}" method="post">
                  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                  <input type="hidden" name="next" value="{{ request.full_path }}">

                  <div class="admin-update-grid">
                    <div class="field">
                      <label for="status-{{ report['id'] }}">Status</label>
                      <select id="status-{{ report['id'] }}" name="status" required>
                        {% for status in statuses %}
                          <option value="{{ status }}" {% if report['status'] == status %}selected{% endif %}>{{ status }}</option>
                        {% endfor %}
                      </select>
                    </div>
                    <div class="field">
                      <label for="public-note-{{ report['id'] }}">Public update note <span class="label-note">optional</span></label>
                      <textarea id="public-note-{{ report['id'] }}" name="public_note" rows="3" maxlength="1000" placeholder="This appears on the report timeline."></textarea>
                    </div>
                    <div class="field">
                      <label for="admin-note-{{ report['id'] }}">Internal note <span class="label-note">private</span></label>
                      <textarea id="admin-note-{{ report['id'] }}" name="admin_note" rows="3" maxlength="2000" placeholder="Only visible to administrators.">{{ report['admin_note'] or '' }}</textarea>
                    </div>
                  </div>

                  <div class="admin-update-footer">
                    <p>Saving a new status adds an entry to the public timeline automatically.</p>
                    <button class="button button-primary" type="submit">Save update</button>
                  </div>
                </form>
              </details>
            </article>
          {% endfor %}
        </div>

        {% if pagination.pages > 1 %}
          <nav class="pagination" aria-label="Admin report pages">
            {% if pagination.has_prev %}
              <a class="pagination-link" href="{{ url_for('admin_dashboard', page=pagination.prev_page, q=filters.q, status=filters.status, issue_type=filters.issue_type, severity=filters.severity) }}">&larr; Previous</a>
            {% else %}
              <span class="pagination-link is-disabled">&larr; Previous</span>
            {% endif %}
            <span class="pagination-status">Page {{ pagination.page }} of {{ pagination.pages }}</span>
            {% if pagination.has_next %}
              <a class="pagination-link" href="{{ url_for('admin_dashboard', page=pagination.next_page, q=filters.q, status=filters.status, issue_type=filters.issue_type, severity=filters.severity) }}">Next &rarr;</a>
            {% else %}
              <span class="pagination-link is-disabled">Next &rarr;</span>
            {% endif %}
          </nav>
        {% endif %}
      {% else %}
        <div class="empty-state">
          <div class="empty-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="52" height="52" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M5 4h14v16H5z"></path>
              <path d="M8 8h8M8 12h8M8 16h5"></path>
            </svg>
          </div>
          <h2>Nothing in this view</h2>
          <p>There are no reports matching those filters right now.</p>
          {% if has_filters %}
            <a class="button button-primary" href="{{ url_for('admin_dashboard') }}">Clear filters</a>
          {% endif %}
        </div>
      {% endif %}
    </div>
  </section>
{% endblock %}
````

### File: static/css/style.css

````css
/* ==========================================================================
   RoadWatch design system
   ========================================================================== */

:root {
  --ink: #14231f;
  --ink-2: #213a31;
  --ink-3: #345248;
  --muted: #5d6b65;
  --muted-light: #5f6c66;
  --paper: #ffffff;
  --paper-soft: #f7f8f4;
  --paper-warm: #f2f4ec;
  --canvas: #edf0e7;
  --line: #dce1d7;
  --line-strong: #c8d0c3;
  --amber: #f2b705;
  --amber-deep: #86650a;
  --amber-soft: #fff5cf;
  --green: #1e7a5a;
  --green-soft: #e4f3eb;
  --blue: #295f9c;
  --blue-soft: #e8f0fa;
  --red: #b33a32;
  --red-soft: #fae9e7;
  --orange: #9c5410;
  --orange-soft: #fdf0df;
  --shadow-xs: 0 1px 2px rgba(20, 35, 31, 0.06);
  --shadow-sm: 0 8px 24px rgba(20, 35, 31, 0.07);
  --shadow-md: 0 18px 50px rgba(20, 35, 31, 0.11);
  --shadow-lg: 0 30px 80px rgba(9, 19, 16, 0.22);
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --container: 1180px;
  --font-sans: "Segoe UI", "Aptos", "Helvetica Neue", Arial, sans-serif;
  --font-mono: "Cascadia Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
  scroll-padding-top: 96px;
}

body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  color: var(--ink);
  background: var(--canvas);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

main {
  flex: 1;
}

img {
  max-width: 100%;
  display: block;
}

a {
  color: inherit;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

h1,
h2,
h3,
p,
dl,
dd,
figure {
  margin-top: 0;
}

h1,
h2,
h3 {
  line-height: 1.12;
  letter-spacing: -0.025em;
}

h1 {
  font-size: clamp(2.5rem, 5vw, 4.6rem);
  font-weight: 750;
}

h2 {
  font-size: clamp(1.7rem, 3vw, 2.5rem);
  font-weight: 720;
}

h3 {
  font-size: 1.2rem;
}

::selection {
  color: var(--ink);
  background: var(--amber);
}

:focus-visible {
  outline: 3px solid #2f7cb4;
  outline-offset: 3px;
}

.container {
  width: min(100% - 48px, var(--container));
  margin-inline: auto;
}

.container.narrow {
  width: min(100% - 48px, 780px);
}

.skip-link {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 1000;
  padding: 10px 16px;
  color: var(--ink);
  background: var(--amber);
  border-radius: 8px;
  font-weight: 700;
  transform: translateY(-150%);
  transition: transform 0.15s ease;
}

.skip-link:focus {
  transform: translateY(0);
}

/* --------------------------------------------------------------------------
   Shared type, buttons, and badges
   -------------------------------------------------------------------------- */

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 14px;
  color: var(--amber-deep);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.13em;
  line-height: 1.35;
  text-transform: uppercase;
}

.eyebrow-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--amber);
  box-shadow: 0 0 0 4px rgba(242, 183, 5, 0.16);
}

.eyebrow-dark {
  color: var(--ink-3);
}

.eyebrow-light {
  color: var(--amber);
}

.text-highlight {
  color: var(--amber);
}

.text-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--ink);
  font-weight: 750;
  text-decoration: none;
  border-bottom: 1px solid rgba(20, 35, 31, 0.25);
  transition: color 0.15s ease, border-color 0.15s ease;
}

.text-link:hover {
  color: var(--green);
  border-color: var(--green);
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 46px;
  padding: 11px 19px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 0.94rem;
  font-weight: 750;
  line-height: 1.2;
  text-align: center;
  text-decoration: none;
  transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.button:hover {
  transform: translateY(-1px);
}

.button:active {
  transform: translateY(0);
}

.button-primary {
  color: var(--ink);
  background: var(--amber);
  border-color: var(--amber);
  box-shadow: 0 5px 16px rgba(201, 149, 0, 0.18);
}

.button-primary:hover {
  background: #ffc61a;
  border-color: #ffc61a;
  box-shadow: 0 8px 22px rgba(201, 149, 0, 0.26);
}

.button-ghost {
  color: var(--ink);
  background: transparent;
  border-color: var(--line-strong);
}

.button-ghost:hover {
  background: var(--paper);
  border-color: #aeb9a9;
}

.button-large {
  min-height: 52px;
  padding-inline: 24px;
  font-size: 1rem;
}

.button-small {
  min-height: 36px;
  padding: 7px 13px;
  font-size: 0.82rem;
}

.button-full {
  width: 100%;
}

.button.is-copied {
  color: var(--paper);
  background: var(--green);
  border-color: var(--green);
}

.status-badge,
.severity-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 0.71rem;
  font-weight: 800;
  letter-spacing: 0.035em;
  line-height: 1.25;
  text-transform: uppercase;
  white-space: nowrap;
}

.status-submitted {
  color: #495b55;
  background: #eef1ed;
  border-color: #dfe5df;
}

.status-under-review {
  color: #7b5900;
  background: var(--amber-soft);
  border-color: #f1dda0;
}

.status-in-progress {
  color: var(--blue);
  background: var(--blue-soft);
  border-color: #cadcf0;
}

.status-resolved {
  color: var(--green);
  background: var(--green-soft);
  border-color: #c8e7d8;
}

.status-rejected {
  color: var(--red);
  background: var(--red-soft);
  border-color: #f0cfcc;
}

.severity-pill {
  color: var(--ink-2);
  background: rgba(255, 255, 255, 0.93);
  border-color: rgba(20, 35, 31, 0.12);
}

.severity-pill-low {
  color: #53625d;
}

.severity-pill-medium {
  color: #7b5900;
  background: #fff7da;
}

.severity-pill-high {
  color: var(--orange);
  background: #fff0df;
}

.severity-pill-critical {
  color: var(--red);
  background: #ffebe8;
}

.tracking-mini {
  font-family: var(--font-mono);
  font-size: 0.76rem;
  letter-spacing: 0.02em;
  color: var(--muted);
}

/* --------------------------------------------------------------------------
   Header and navigation
   -------------------------------------------------------------------------- */

.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(247, 248, 244, 0.92);
  border-bottom: 1px solid rgba(200, 208, 195, 0.72);
  backdrop-filter: blur(14px);
}

.nav-shell {
  position: relative;
  min-height: 76px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--ink);
  text-decoration: none;
}

.brand img {
  border-radius: 12px;
  box-shadow: var(--shadow-xs);
}

.brand-name {
  font-size: 1.23rem;
  font-weight: 800;
  letter-spacing: -0.035em;
}

.brand-name span {
  color: var(--amber-deep);
}

.brand-light {
  color: var(--paper);
}

.brand-light .brand-name span {
  color: var(--amber);
}

.site-nav {
  display: flex;
  align-items: center;
  gap: 26px;
}

.site-nav > a {
  position: relative;
  color: var(--ink-3);
  font-size: 0.9rem;
  font-weight: 650;
  text-decoration: none;
}

.site-nav > a:hover,
.site-nav > a.is-active {
  color: var(--ink);
}

.site-nav > a.is-active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -9px;
  height: 2px;
  background: var(--amber);
  border-radius: 2px;
}

.site-nav .nav-login {
  padding: 9px 15px;
  color: var(--paper);
  background: var(--ink);
  border-radius: 999px;
}

.site-nav .nav-login:hover,
.site-nav .nav-login.is-active {
  color: var(--paper);
  background: var(--ink-2);
}

.site-nav .nav-login.is-active::after {
  display: none;
}

.nav-account {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 20px;
  border-left: 1px solid var(--line);
}

.nav-account form {
  margin: 0;
}

.nav-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-3);
  font-size: 0.82rem;
  font-weight: 650;
}

.avatar {
  display: inline-grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  color: var(--ink);
  background: var(--amber);
  border-radius: 50%;
  font-size: 0.86rem;
  font-weight: 850;
  letter-spacing: 0.02em;
}

.avatar-sm {
  width: 30px;
  height: 30px;
  font-size: 0.68rem;
}

.nav-toggle {
  display: none;
  align-items: center;
  gap: 9px;
  padding: 9px 12px;
  color: var(--ink);
  background: transparent;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 750;
}

.nav-toggle-icon {
  display: grid;
  gap: 3px;
  width: 15px;
}

.nav-toggle-icon span {
  height: 1.5px;
  background: currentColor;
  border-radius: 2px;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.nav-toggle.is-open .nav-toggle-icon span:nth-child(1) {
  transform: translateY(4.5px) rotate(45deg);
}

.nav-toggle.is-open .nav-toggle-icon span:nth-child(2) {
  opacity: 0;
}

.nav-toggle.is-open .nav-toggle-icon span:nth-child(3) {
  transform: translateY(-4.5px) rotate(-45deg);
}

/* --------------------------------------------------------------------------
   Flash messages
   -------------------------------------------------------------------------- */

.flash-stack {
  position: relative;
  z-index: 20;
  margin-top: 20px;
  display: grid;
  gap: 9px;
}

.flash {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 13px 15px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.flash p {
  flex: 1;
  margin: 0;
  color: var(--ink-2);
  font-size: 0.9rem;
  font-weight: 600;
}

.flash-marker {
  width: 9px;
  height: 9px;
  margin-top: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--blue);
}

.flash-success .flash-marker {
  background: var(--green);
}

.flash-error .flash-marker {
  background: var(--red);
}

.flash-info .flash-marker {
  background: var(--blue);
}

.flash-close {
  width: 26px;
  height: 26px;
  padding: 0;
  color: var(--muted);
  background: transparent;
  border: 0;
  border-radius: 50%;
  font-size: 1.25rem;
  line-height: 1;
}

.flash-close:hover {
  color: var(--ink);
  background: var(--paper-warm);
}

/* --------------------------------------------------------------------------
   Home hero and tracker
   -------------------------------------------------------------------------- */

.hero {
  position: relative;
  overflow: hidden;
  padding: 82px 0 74px;
  color: var(--paper);
  background:
    radial-gradient(circle at 78% 18%, rgba(242, 183, 5, 0.16), transparent 26%),
    radial-gradient(circle at 8% 96%, rgba(70, 125, 103, 0.3), transparent 33%),
    linear-gradient(130deg, #101f1b 0%, #142820 52%, #1b332a 100%);
}

.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 100% 72px;
  mask-image: linear-gradient(to bottom, transparent, black 32%, transparent);
}

.hero-road {
  position: absolute;
  right: -12%;
  bottom: -210px;
  width: 63%;
  height: 500px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 55% 0 0 0;
  transform: rotate(-9deg);
  opacity: 0.6;
}

.hero-road::before,
.hero-road::after {
  content: "";
  position: absolute;
  border-radius: inherit;
}

.hero-road::before {
  inset: 42px;
  border: 1px dashed rgba(242, 183, 5, 0.25);
}

.hero-road::after {
  inset: 95px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.hero-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.28fr) minmax(330px, 0.78fr);
  align-items: center;
  gap: 68px;
}

.hero-copy h1 {
  max-width: 720px;
  margin-bottom: 22px;
  color: var(--paper);
  font-size: clamp(3rem, 5.6vw, 5rem);
  font-weight: 780;
  letter-spacing: -0.045em;
  line-height: 0.98;
}

.hero-lead {
  max-width: 620px;
  margin-bottom: 29px;
  color: rgba(247, 248, 244, 0.76);
  font-size: 1.08rem;
  line-height: 1.72;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.hero .button-primary {
  color: var(--ink);
}

.hero .button-ghost {
  color: var(--paper);
  background: rgba(255, 255, 255, 0.045);
  border-color: rgba(255, 255, 255, 0.23);
}

.hero .button-ghost:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.4);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  margin: 52px 0 0;
  padding-top: 27px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.hero-stats div {
  padding: 0 18px;
  border-left: 1px solid rgba(255, 255, 255, 0.12);
}

.hero-stats div:first-child {
  padding-left: 0;
  border-left: 0;
}

.hero-stats dt {
  color: rgba(247, 248, 244, 0.55);
  font-size: 0.69rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-stats dd {
  margin: 3px 0 0;
  color: var(--paper);
  font-size: 1.7rem;
  font-weight: 780;
  line-height: 1.2;
}

.tracker-card {
  position: relative;
  padding: 32px;
  color: var(--ink);
  background: var(--paper-soft);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.tracker-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 32px;
  right: 32px;
  height: 3px;
  background: linear-gradient(90deg, var(--amber), transparent);
  border-radius: 0 0 4px 4px;
}

.tracker-icon {
  display: grid;
  place-items: center;
  width: 50px;
  height: 50px;
  margin-bottom: 22px;
  color: var(--ink);
  background: var(--amber);
  border-radius: 16px;
  box-shadow: 0 7px 18px rgba(201, 149, 0, 0.24);
}

.tracker-card h2 {
  margin-bottom: 9px;
  font-size: 1.65rem;
}

.tracker-card > p:not(.eyebrow) {
  margin-bottom: 20px;
  color: var(--muted);
  font-size: 0.92rem;
}

.tracker-form label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.055em;
  text-transform: uppercase;
}

.input-button-row {
  display: flex;
  gap: 8px;
}

.input-button-row input {
  min-width: 0;
  flex: 1;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  text-transform: uppercase;
}

.input-button-row .button {
  flex: 0 0 auto;
  border-radius: 11px;
}

.tracker-divider {
  height: 1px;
  margin: 27px 0 22px;
  background: var(--line);
}

.tracker-card h3 {
  margin-bottom: 14px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mini-steps {
  display: grid;
  gap: 11px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.mini-steps li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.mini-steps li > span {
  display: grid;
  place-items: center;
  width: 23px;
  height: 23px;
  flex: 0 0 auto;
  margin-top: 1px;
  color: var(--ink);
  background: #e9ede3;
  border-radius: 50%;
  font-size: 0.69rem;
  font-weight: 850;
}

.mini-steps p {
  margin: 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.48;
}

.mini-steps strong {
  color: var(--ink-2);
}

/* --------------------------------------------------------------------------
   Report form
   -------------------------------------------------------------------------- */

.section {
  padding: 86px 0;
}

.section-tight {
  padding-top: 48px;
}

.report-section {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.4), transparent 180px),
    var(--paper-warm);
  border-top: 1px solid var(--line);
}

.report-layout {
  display: grid;
  grid-template-columns: minmax(240px, 0.72fr) minmax(0, 1.4fr);
  align-items: start;
  gap: 64px;
}

.section-intro {
  position: sticky;
  top: 112px;
  padding-top: 18px;
}

.section-intro h2 {
  max-width: 430px;
  margin-bottom: 20px;
}

.section-intro > p:not(.eyebrow) {
  margin-bottom: 24px;
  color: var(--muted);
  font-size: 1rem;
  line-height: 1.7;
}

.check-list {
  display: grid;
  gap: 12px;
  margin: 0 0 28px;
  padding: 0;
  list-style: none;
}

.check-list li {
  position: relative;
  padding-left: 30px;
  color: var(--ink-3);
  font-size: 0.91rem;
  font-weight: 600;
}

.check-list li::before {
  content: "✓";
  position: absolute;
  top: 0;
  left: 0;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  color: var(--green);
  background: var(--green-soft);
  border-radius: 50%;
  font-size: 0.72rem;
  font-weight: 900;
}

.safety-note {
  padding: 18px 20px;
  background: #fffaf0;
  border: 1px solid #eddfba;
  border-left: 3px solid var(--amber);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.safety-note strong {
  display: block;
  margin-bottom: 3px;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.safety-note p {
  margin: 0;
  color: #6f6245;
  font-size: 0.83rem;
  line-height: 1.55;
}

.card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.form-card {
  overflow: hidden;
}

.form-section {
  margin: 0;
  padding: 34px 36px;
  border: 0;
  border-bottom: 1px solid var(--line);
}

.form-section legend {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 24px;
  padding: 0;
}

.form-section legend > span:last-child {
  display: grid;
  gap: 2px;
}

.form-section legend strong {
  font-size: 1.08rem;
  letter-spacing: -0.01em;
}

.form-section legend small {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 400;
  line-height: 1.45;
}

.step-number {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  color: var(--ink);
  background: var(--amber-soft);
  border: 1px solid #f1dda0;
  border-radius: 12px;
  font-family: var(--font-mono);
  font-size: 0.73rem;
  font-weight: 800;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.field {
  min-width: 0;
}

.field-full {
  grid-column: 1 / -1;
}

.field label,
.field legend,
.field .field-label,
.severity-field > legend {
  display: block;
  margin-bottom: 7px;
  color: var(--ink-2);
  font-size: 0.82rem;
  font-weight: 750;
}

.field label span[aria-hidden="true"],
.field legend span[aria-hidden="true"] {
  color: var(--red);
}

.severity-field {
  margin-bottom: 0;
  padding: 0;
  border: 0;
}

.label-note {
  margin-left: 4px;
  color: var(--muted-light);
  font-size: 0.72rem;
  font-weight: 550;
}

.label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.label-row .label-note {
  font-family: var(--font-mono);
}

input,
select,
textarea {
  width: 100%;
  color: var(--ink);
  background: var(--paper-soft);
  border: 1px solid var(--line-strong);
  border-radius: 11px;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

input,
select {
  min-height: 48px;
  padding: 10px 13px;
}

textarea {
  min-height: 118px;
  padding: 12px 13px;
  resize: vertical;
}

input::placeholder,
textarea::placeholder {
  color: #9aa49f;
}

input:hover,
select:hover,
textarea:hover {
  background: var(--paper);
}

input:focus,
select:focus,
textarea:focus {
  background: var(--paper);
  border-color: var(--ink-3);
  outline: 0;
  box-shadow: 0 0 0 3px rgba(52, 82, 72, 0.13);
}

.severity-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.severity-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-height: 82px;
  padding: 13px;
  background: var(--paper-soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.severity-card input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.severity-card:hover {
  background: var(--paper);
  border-color: var(--line-strong);
}

.severity-card:focus-within {
  outline: 3px solid #2f7cb4;
  outline-offset: 2px;
}

.severity-card:has(input:checked) {
  background: var(--paper);
  border-color: var(--ink-3);
  box-shadow: inset 0 0 0 1px var(--ink-3);
}

.severity-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  margin-top: 4px;
  border-radius: 50%;
  background: var(--muted-light);
  box-shadow: 0 0 0 4px rgba(102, 117, 111, 0.1);
}

.severity-low .severity-dot {
  background: #7d9188;
}

.severity-medium .severity-dot {
  background: var(--amber-deep);
  box-shadow: 0 0 0 4px rgba(201, 149, 0, 0.12);
}

.severity-high .severity-dot {
  background: var(--orange);
  box-shadow: 0 0 0 4px rgba(183, 101, 22, 0.12);
}

.severity-critical .severity-dot {
  background: var(--red);
  box-shadow: 0 0 0 4px rgba(179, 58, 50, 0.12);
}

.severity-copy {
  display: grid;
  gap: 3px;
}

.severity-copy strong {
  font-size: 0.83rem;
}

.severity-copy small {
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.4;
}

.file-drop {
  display: flex !important;
  align-items: center;
  gap: 14px;
  margin: 0 !important;
  padding: 18px;
  background: var(--paper-soft);
  border: 1px dashed var(--line-strong);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.file-drop:hover,
.file-drop:focus-within {
  background: var(--paper);
  border-color: var(--ink-3);
}

.file-drop input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  opacity: 0;
  pointer-events: none;
}

.file-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  color: var(--ink-3);
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.file-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.file-copy strong {
  font-size: 0.85rem;
}

.file-copy small {
  color: var(--muted);
  font-size: 0.74rem;
}

.file-name {
  max-width: 100%;
  overflow: hidden;
  color: var(--muted-light);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-name.has-file {
  color: var(--green);
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 36px;
  background: var(--paper-soft);
}

.form-footer p {
  max-width: 440px;
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.55;
}

.form-footer .button {
  flex: 0 0 auto;
}

/* --------------------------------------------------------------------------
   Recent reports and shared report cards
   -------------------------------------------------------------------------- */

.recent-section {
  background: var(--paper-soft);
  border-top: 1px solid var(--line);
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  margin-bottom: 30px;
}

.section-heading h2 {
  margin-bottom: 0;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
}

.report-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xs);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.report-card:hover {
  border-color: var(--line-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.report-card-media {
  position: relative;
  display: block;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #dfe6dc;
}

.report-card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.report-card:hover .report-card-media img {
  transform: scale(1.025);
}

.report-card-media .status-badge {
  position: absolute;
  top: 13px;
  left: 13px;
  box-shadow: 0 2px 8px rgba(20, 35, 31, 0.1);
}

.report-card-media .severity-pill {
  position: absolute;
  top: 13px;
  right: 13px;
  box-shadow: 0 2px 8px rgba(20, 35, 31, 0.1);
}

.report-card-placeholder {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  color: rgba(20, 35, 31, 0.34);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.28), transparent),
    repeating-linear-gradient(
      115deg,
      #dfe6dc,
      #dfe6dc 12px,
      #e6ebe2 12px,
      #e6ebe2 24px
    );
}

.report-card-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 20px;
}

.report-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 9px;
  color: var(--muted);
  font-size: 0.69rem;
  font-weight: 700;
  letter-spacing: 0.035em;
  text-transform: uppercase;
}

.report-card-meta span:first-child {
  color: var(--amber-deep);
}

.report-card-meta span:last-child {
  text-align: right;
}

.report-card h2,
.report-card h3 {
  margin-bottom: 9px;
  font-size: 1.23rem;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.report-card h2 a,
.report-card h3 a {
  text-decoration: none;
}

.report-card h2 a:hover,
.report-card h3 a:hover {
  color: var(--green);
}

.report-location {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 18px;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.45;
}

.report-location svg {
  flex: 0 0 auto;
  margin-top: 2px;
  color: var(--muted-light);
}

.report-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding-top: 15px;
  border-top: 1px solid var(--line);
}

.report-card-footer .text-link {
  font-size: 0.82rem;
}

/* --------------------------------------------------------------------------
   Public reports page
   -------------------------------------------------------------------------- */

.page-hero {
  padding: 56px 0 44px;
  background:
    radial-gradient(circle at 85% 20%, rgba(242, 183, 5, 0.11), transparent 25%),
    var(--paper-soft);
  border-bottom: 1px solid var(--line);
}

.page-hero-inner {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 36px;
}

.page-hero h1 {
  margin-bottom: 10px;
  font-size: clamp(2.4rem, 4vw, 3.6rem);
}

.page-hero p:not(.eyebrow) {
  max-width: 650px;
  margin-bottom: 0;
  color: var(--muted);
}

.filters-card {
  display: grid;
  grid-template-columns: minmax(230px, 1.45fr) repeat(3, minmax(130px, 0.75fr)) auto;
  align-items: end;
  gap: 14px;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.filters-card .field label {
  font-size: 0.72rem;
  letter-spacing: 0.045em;
  text-transform: uppercase;
}

.filters-card input,
.filters-card select {
  min-height: 44px;
  background: var(--paper-soft);
  font-size: 0.84rem;
}

.input-with-icon {
  position: relative;
}

.input-with-icon svg {
  position: absolute;
  top: 50%;
  left: 13px;
  color: var(--muted-light);
  transform: translateY(-50%);
  pointer-events: none;
}

.input-with-icon input {
  padding-left: 39px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.filter-actions .button {
  min-height: 44px;
  padding-inline: 17px;
  font-size: 0.83rem;
}

.results-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin: 20px 0 22px;
}

.results-bar p {
  margin: 0;
  color: var(--muted);
  font-size: 0.84rem;
}

.results-bar strong {
  color: var(--ink);
}

.results-query {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-grid-wide {
  margin-bottom: 8px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  margin-top: 38px;
}

.pagination-link {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 7px 15px;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
}

.pagination-link:hover {
  border-color: var(--ink-3);
}

.pagination-link.is-disabled {
  color: var(--muted-light);
  background: transparent;
  border-color: var(--line);
}

.pagination-status {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 650;
}

.empty-state {
  display: grid;
  justify-items: center;
  padding: 64px 24px;
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-lg);
  text-align: center;
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 92px;
  height: 92px;
  margin-bottom: 18px;
  color: var(--muted-light);
  background: var(--paper-soft);
  border-radius: 50%;
}

.empty-state h2 {
  margin-bottom: 8px;
  font-size: 1.55rem;
}

.empty-state p {
  max-width: 420px;
  margin-bottom: 21px;
  color: var(--muted);
  font-size: 0.92rem;
}

/* --------------------------------------------------------------------------
   Report detail
   -------------------------------------------------------------------------- */

.detail-hero {
  padding: 38px 0 42px;
  background:
    linear-gradient(90deg, rgba(242, 183, 5, 0.08), transparent 40%),
    var(--paper-soft);
  border-bottom: 1px solid var(--line);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 27px;
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
}

.back-link:hover {
  color: var(--ink);
}

.detail-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 38px;
}

.detail-kicker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.issue-label {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.detail-heading h1 {
  max-width: 820px;
  margin-bottom: 12px;
  font-size: clamp(2.2rem, 4.5vw, 3.9rem);
}

.detail-location {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 0;
  color: var(--muted);
  font-size: 0.94rem;
}

.detail-location svg {
  color: var(--muted-light);
}

.detail-tracking {
  display: grid;
  flex: 0 0 auto;
  gap: 2px;
  min-width: 235px;
  padding: 16px 18px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-xs);
}

.detail-tracking > span {
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-tracking strong {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  letter-spacing: 0.02em;
}

.detail-tracking .button {
  justify-self: start;
  margin-top: 7px;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(290px, 0.72fr);
  align-items: start;
  gap: 38px;
}

.detail-main {
  display: grid;
  gap: 24px;
}

.detail-photo {
  overflow: hidden;
  margin: 0;
  background: var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.detail-photo img {
  width: 100%;
  max-height: 600px;
  object-fit: cover;
}

.detail-card {
  padding: 32px;
}

.detail-card h2 {
  margin-bottom: 16px;
  font-size: 1.45rem;
}

.description-text {
  color: var(--ink-3);
  font-size: 1rem;
  line-height: 1.75;
  white-space: pre-line;
}

.detail-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  margin: 28px 0 0;
  overflow: hidden;
  background: var(--line);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.detail-facts div {
  padding: 15px 17px;
  background: var(--paper-soft);
}

.detail-facts dt {
  margin-bottom: 3px;
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 750;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.detail-facts dd {
  margin: 0;
  font-size: 0.87rem;
  font-weight: 650;
}

.severity-text {
  font-weight: 750;
}

.severity-text-low {
  color: var(--muted);
}

.severity-text-medium {
  color: var(--amber-deep);
}

.severity-text-high {
  color: var(--orange);
}

.severity-text-critical {
  color: var(--red);
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 24px;
}

.detail-sidebar {
  display: grid;
  gap: 20px;
}

.status-card {
  padding: 27px;
}

.status-card > .eyebrow {
  margin-bottom: 11px;
}

.current-status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.current-status strong {
  font-size: 1.32rem;
  letter-spacing: -0.02em;
}

.status-pulse {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--muted);
  box-shadow: 0 0 0 5px rgba(102, 117, 111, 0.11);
}

.status-panel-under-review .status-pulse {
  background: var(--amber-deep);
  box-shadow: 0 0 0 5px rgba(201, 149, 0, 0.14);
}

.status-panel-in-progress .status-pulse {
  background: var(--blue);
  box-shadow: 0 0 0 5px rgba(41, 95, 156, 0.12);
}

.status-panel-resolved .status-pulse {
  background: var(--green);
  box-shadow: 0 0 0 5px rgba(30, 122, 90, 0.13);
}

.status-panel-rejected .status-pulse {
  background: var(--red);
  box-shadow: 0 0 0 5px rgba(179, 58, 50, 0.12);
}

.status-help {
  margin-bottom: 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.55;
}

.timeline-wrap {
  margin-top: 25px;
  padding-top: 23px;
  border-top: 1px solid var(--line);
}

.timeline-wrap h2 {
  margin-bottom: 18px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.timeline {
  position: relative;
  display: grid;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 14px;
  padding-bottom: 21px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-item::before {
  content: "";
  position: absolute;
  top: 15px;
  bottom: -2px;
  left: 5px;
  width: 1px;
  background: var(--line);
}

.timeline-item:last-child::before {
  display: none;
}

.timeline-dot {
  position: relative;
  z-index: 1;
  width: 11px;
  height: 11px;
  flex: 0 0 auto;
  margin-top: 5px;
  background: var(--muted-light);
  border: 2px solid var(--paper);
  border-radius: 50%;
  box-shadow: 0 0 0 1px var(--line-strong);
}

.timeline-dot-under-review {
  background: var(--amber-deep);
}

.timeline-dot-in-progress {
  background: var(--blue);
}

.timeline-dot-resolved {
  background: var(--green);
}

.timeline-dot-rejected {
  background: var(--red);
}

.timeline-content {
  min-width: 0;
}

.timeline-head {
  display: grid;
  gap: 1px;
}

.timeline-head strong {
  font-size: 0.82rem;
}

.timeline-head time {
  color: var(--muted-light);
  font-size: 0.66rem;
  font-weight: 650;
}

.timeline-content p {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.5;
}

.timeline-author {
  display: inline-block;
  margin-top: 5px;
  color: var(--muted-light);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.help-card {
  padding: 25px;
  color: var(--paper);
  background:
    radial-gradient(circle at 100% 0, rgba(242, 183, 5, 0.2), transparent 42%),
    var(--ink);
  border-radius: var(--radius-md);
}

.help-card h2 {
  margin-bottom: 8px;
  font-size: 1.2rem;
}

.help-card p {
  margin-bottom: 15px;
  color: rgba(255, 255, 255, 0.67);
  font-size: 0.82rem;
}

.help-card .text-link {
  color: var(--amber);
  border-color: rgba(242, 183, 5, 0.35);
}

.help-card .text-link:hover {
  color: var(--paper);
  border-color: var(--paper);
}

/* --------------------------------------------------------------------------
   Submission confirmation
   -------------------------------------------------------------------------- */

.confirmation-section {
  background:
    radial-gradient(circle at 50% 0, rgba(242, 183, 5, 0.12), transparent 30%),
    var(--paper-warm);
  border-bottom: 1px solid var(--line);
}

.confirmation-card {
  padding: clamp(30px, 6vw, 56px);
  text-align: center;
}

.success-mark {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  margin: 0 auto 22px;
  color: var(--green);
  background: var(--green-soft);
  border: 1px solid #c8e7d8;
  border-radius: 50%;
  box-shadow: 0 0 0 10px rgba(30, 122, 90, 0.06);
}

.confirmation-card .eyebrow {
  justify-content: center;
}

.confirmation-card h1 {
  margin-bottom: 14px;
  font-size: clamp(2.2rem, 5vw, 3.5rem);
}

.confirmation-lead {
  max-width: 580px;
  margin: 0 auto 28px;
  color: var(--muted);
  font-size: 1rem;
}

.tracking-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  max-width: 610px;
  margin: 0 auto;
  padding: 18px 20px;
  color: var(--paper);
  background:
    radial-gradient(circle at 100% 0, rgba(242, 183, 5, 0.18), transparent 45%),
    var(--ink);
  border-radius: var(--radius-md);
  text-align: left;
}

.tracking-box > div {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.tracking-box span {
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.67rem;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tracking-box strong {
  overflow-wrap: anywhere;
  color: var(--amber);
  font-family: var(--font-mono);
  font-size: clamp(1.1rem, 3.5vw, 1.55rem);
  letter-spacing: 0.04em;
}

.tracking-warning {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 0.78rem;
}

.confirmation-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  max-width: 610px;
  margin: 32px auto;
  overflow: hidden;
  background: var(--line);
  border: 1px solid var(--line);
  border-radius: 12px;
  text-align: left;
}

.confirmation-summary > div {
  padding: 14px 17px;
  background: var(--paper-soft);
}

.confirmation-summary span:not(.status-badge) {
  display: block;
  margin-bottom: 2px;
  color: var(--muted);
  font-size: 0.66rem;
  font-weight: 750;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.confirmation-summary strong {
  font-size: 0.84rem;
  line-height: 1.4;
}

.confirmation-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.confirmation-actions .text-link {
  margin-inline: 7px;
  font-size: 0.83rem;
}

.next-steps {
  margin-top: 32px;
  padding: 5px 20px;
}

.next-steps h2 {
  margin-bottom: 17px;
  font-size: 1rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.next-steps-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.next-steps-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.next-step-number {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  color: var(--ink);
  background: var(--amber);
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 850;
}

.next-steps-list p {
  margin: 0;
  color: var(--muted);
  font-size: 0.79rem;
  line-height: 1.55;
}

.next-steps-list strong {
  color: var(--ink-2);
}

/* --------------------------------------------------------------------------
   Login
   -------------------------------------------------------------------------- */

.auth-section {
  position: relative;
  overflow: hidden;
  min-height: 640px;
  padding: 74px 0;
  color: var(--paper);
  background:
    radial-gradient(circle at 82% 20%, rgba(242, 183, 5, 0.16), transparent 25%),
    linear-gradient(128deg, #101f1b, #1c372d 72%, #214035);
}

.auth-backdrop {
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(
      112deg,
      transparent,
      transparent 86px,
      rgba(255, 255, 255, 0.025) 86px,
      rgba(255, 255, 255, 0.025) 87px
    );
  pointer-events: none;
}

.auth-shell {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 430px);
  align-items: center;
  gap: 84px;
}

.auth-intro h1 {
  max-width: 560px;
  margin-bottom: 20px;
  font-size: clamp(2.7rem, 5.5vw, 4.5rem);
}

.auth-intro > p:not(.eyebrow) {
  max-width: 500px;
  margin-bottom: 27px;
  color: rgba(255, 255, 255, 0.67);
  font-size: 1rem;
}

.auth-points {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  color: rgba(255, 255, 255, 0.82);
  font-size: 0.9rem;
  list-style: none;
}

.auth-points li {
  position: relative;
  padding-left: 25px;
}

.auth-points li::before {
  content: "";
  position: absolute;
  top: 9px;
  left: 2px;
  width: 7px;
  height: 7px;
  background: var(--amber);
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(242, 183, 5, 0.13);
}

.auth-card {
  padding: 34px;
  color: var(--ink);
  box-shadow: var(--shadow-lg);
}

.auth-mark {
  display: grid;
  place-items: center;
  width: 66px;
  height: 66px;
  margin-bottom: 21px;
  background: var(--paper-soft);
  border: 1px solid var(--line);
  border-radius: 18px;
}

.auth-card h2 {
  margin-bottom: 6px;
  font-size: 1.8rem;
}

.auth-subtitle {
  margin-bottom: 24px;
  color: var(--muted);
  font-size: 0.87rem;
}

.auth-card .field {
  margin-bottom: 16px;
}

.auth-card .button {
  margin-top: 2px;
}

.auth-help {
  margin: 22px 0 14px;
  padding-top: 18px;
  color: var(--muted);
  border-top: 1px solid var(--line);
  font-size: 0.76rem;
  text-align: center;
}

.auth-home-link {
  display: flex;
  justify-content: center;
  font-size: 0.8rem;
}

/* --------------------------------------------------------------------------
   Admin dashboard
   -------------------------------------------------------------------------- */

.dashboard-hero {
  padding: 50px 0 42px;
  color: var(--paper);
  background:
    radial-gradient(circle at 86% 5%, rgba(242, 183, 5, 0.16), transparent 25%),
    linear-gradient(130deg, #101f1b, #1a3128);
}

.dashboard-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  margin-bottom: 34px;
}

.dashboard-heading h1 {
  margin-bottom: 9px;
  font-size: clamp(2.4rem, 4.5vw, 3.7rem);
}

.dashboard-heading p:not(.eyebrow) {
  max-width: 600px;
  margin-bottom: 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 0.93rem;
}

.dashboard-user {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px 15px 10px 11px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.13);
  border-radius: 999px;
}

.dashboard-user > div {
  display: grid;
  gap: 0;
}

.dashboard-user span:not(.avatar) {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.63rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.dashboard-user strong {
  font-size: 0.8rem;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 17px;
  background: rgba(255, 255, 255, 0.065);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-md);
}

.stat-icon {
  display: grid;
  place-items: center;
  width: 43px;
  height: 43px;
  flex: 0 0 auto;
  color: var(--paper);
  background: rgba(255, 255, 255, 0.09);
  border-radius: 12px;
}

.stat-icon-amber {
  color: var(--amber);
  background: rgba(242, 183, 5, 0.12);
}

.stat-icon-red {
  color: #ffada5;
  background: rgba(179, 58, 50, 0.2);
}

.stat-icon-green {
  color: #8bdeb9;
  background: rgba(30, 122, 90, 0.22);
}

.stat-card > div {
  display: grid;
  gap: 0;
}

.stat-card span:not(.stat-icon) {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.065em;
  text-transform: uppercase;
}

.stat-card strong {
  font-size: 1.55rem;
  line-height: 1.2;
}

.admin-filters {
  grid-template-columns: minmax(230px, 1.4fr) repeat(3, minmax(125px, 0.7fr)) auto;
}

.admin-list {
  display: grid;
  gap: 14px;
}

.admin-report {
  overflow: hidden;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xs);
}

.admin-report-top {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr) auto;
  align-items: start;
  gap: 19px;
  padding: 20px;
}

.admin-thumb {
  width: 112px;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--paper-warm);
  border-radius: 10px;
}

.admin-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.admin-thumb > span {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  color: var(--muted-light);
  background: repeating-linear-gradient(
    115deg,
    #e9ede5,
    #e9ede5 10px,
    #eef1e9 10px,
    #eef1e9 20px
  );
}

.admin-report-copy {
  min-width: 0;
}

.admin-report-kicker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin-bottom: 7px;
}

.admin-report h2 {
  margin-bottom: 4px;
  font-size: 1.2rem;
  line-height: 1.3;
}

.admin-report h2 a {
  text-decoration: none;
}

.admin-report h2 a:hover {
  color: var(--green);
}

.admin-location {
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 0.78rem;
}

.admin-description {
  display: -webkit-box;
  overflow: hidden;
  margin-bottom: 9px;
  color: var(--ink-3);
  font-size: 0.81rem;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.admin-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 15px;
  color: var(--muted);
  font-size: 0.7rem;
}

.admin-meta strong {
  color: var(--ink-3);
  font-weight: 750;
}

.admin-meta a {
  color: var(--blue);
  text-decoration: none;
}

.admin-meta a:hover {
  text-decoration: underline;
}

.internal-note {
  margin: 9px 0 0;
  padding: 7px 10px;
  color: #6f6245;
  background: #fffaf0;
  border-left: 2px solid var(--amber);
  border-radius: 0 6px 6px 0;
  font-size: 0.73rem;
  line-height: 1.45;
}

.admin-report-links {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.admin-update {
  border-top: 1px solid var(--line);
  background: var(--paper-soft);
}

.admin-update summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 13px 20px;
  color: var(--ink-2);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 750;
  list-style: none;
  user-select: none;
}

.admin-update summary::-webkit-details-marker {
  display: none;
}

.admin-update summary > span:first-child {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.admin-update summary > span:first-child::before {
  content: "+";
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  font-size: 0.9rem;
  line-height: 1;
}

.admin-update[open] summary > span:first-child::before {
  content: "−";
}

.summary-hint {
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 500;
}

.admin-update form {
  padding: 0 20px 20px;
}

.admin-update-grid {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr) minmax(0, 1fr);
  gap: 13px;
  padding: 17px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.admin-update-grid .field label {
  font-size: 0.72rem;
}

.admin-update-grid input,
.admin-update-grid select,
.admin-update-grid textarea {
  min-height: 42px;
  background: var(--paper-soft);
  font-size: 0.82rem;
}

.admin-update-grid textarea {
  min-height: 82px;
}

.admin-update-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 13px;
}

.admin-update-footer p {
  margin: 0;
  color: var(--muted);
  font-size: 0.72rem;
}

.admin-update-footer .button {
  flex: 0 0 auto;
}

/* --------------------------------------------------------------------------
   Error page
   -------------------------------------------------------------------------- */

.error-section {
  background:
    radial-gradient(circle at 50% 10%, rgba(242, 183, 5, 0.12), transparent 30%),
    var(--paper-warm);
}

.error-card {
  padding: clamp(32px, 6vw, 58px);
  text-align: center;
}

.error-code {
  display: block;
  margin-bottom: 12px;
  color: var(--line-strong);
  font-family: var(--font-mono);
  font-size: clamp(4rem, 12vw, 8rem);
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -0.08em;
}

.error-card .eyebrow {
  justify-content: center;
}

.error-card h1 {
  margin-bottom: 13px;
  font-size: clamp(2rem, 4vw, 3rem);
}

.error-card > p:not(.eyebrow) {
  max-width: 500px;
  margin: 0 auto 25px;
  color: var(--muted);
}

.error-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 9px;
}

/* --------------------------------------------------------------------------
   Footer
   -------------------------------------------------------------------------- */

.site-footer {
  margin-top: auto;
  padding: 54px 0 23px;
  color: rgba(255, 255, 255, 0.64);
  background:
    radial-gradient(circle at 10% 100%, rgba(60, 109, 90, 0.22), transparent 32%),
    #0f1d18;
}

.footer-grid {
  display: grid;
  grid-template-columns: minmax(240px, 1.5fr) repeat(2, minmax(130px, 0.55fr));
  gap: 48px;
  padding-bottom: 38px;
}

.footer-brand p {
  max-width: 320px;
  margin: 14px 0 0;
  font-size: 0.83rem;
  line-height: 1.6;
}

.footer-links {
  display: grid;
  align-content: start;
  gap: 8px;
}

.footer-links h2 {
  margin-bottom: 4px;
  color: var(--paper);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.footer-links a {
  width: fit-content;
  color: rgba(255, 255, 255, 0.66);
  font-size: 0.82rem;
  text-decoration: none;
}

.footer-links a:hover {
  color: var(--amber);
}

.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-bottom p {
  margin: 0;
  font-size: 0.72rem;
}

/* --------------------------------------------------------------------------
   Responsive
   -------------------------------------------------------------------------- */

@media (max-width: 1060px) {
  .hero-grid {
    gap: 44px;
  }

  .report-layout {
    gap: 40px;
  }

  .filters-card,
  .admin-filters {
    grid-template-columns: minmax(210px, 1.4fr) repeat(2, minmax(130px, 0.75fr));
  }

  .filters-card .field:nth-of-type(4) {
    grid-column: 1 / 2;
  }

  .filter-actions {
    align-self: end;
  }

  .admin-update-grid {
    grid-template-columns: 170px minmax(0, 1fr);
  }

  .admin-update-grid .field:last-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 940px) {
  .hero {
    padding-top: 64px;
  }

  .hero-grid {
    grid-template-columns: 1fr;
    gap: 42px;
  }

  .hero-copy {
    max-width: 720px;
  }

  .hero-copy h1 {
    max-width: 720px;
  }

  .tracker-card {
    max-width: 590px;
  }

  .report-layout {
    grid-template-columns: 1fr;
  }

  .section-intro {
    position: static;
    max-width: 660px;
    padding-top: 0;
  }

  .section-intro h2 {
    max-width: 620px;
  }

  .report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-sidebar {
    grid-template-columns: minmax(0, 1fr) minmax(250px, 0.6fr);
    align-items: start;
  }

  .auth-shell {
    grid-template-columns: 1fr;
    gap: 42px;
  }

  .auth-intro {
    max-width: 640px;
  }

  .auth-card {
    width: min(100%, 480px);
  }

  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .admin-report-top {
    grid-template-columns: 96px minmax(0, 1fr);
  }

  .admin-thumb {
    width: 96px;
  }

  .admin-report-links {
    grid-column: 2;
    flex-direction: row;
  }

  .footer-grid {
    grid-template-columns: minmax(220px, 1.4fr) repeat(2, minmax(120px, 0.6fr));
    gap: 30px;
  }
}

@media (max-width: 820px) {
  .container,
  .container.narrow {
    width: min(100% - 36px, var(--container));
  }

  .nav-shell {
    min-height: 68px;
  }

  .nav-toggle {
    display: inline-flex;
  }

  .site-nav {
    position: absolute;
    top: calc(100% + 10px);
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    align-items: stretch;
    gap: 2px;
    padding: 12px;
    background: var(--paper-soft);
    border: 1px solid var(--line-strong);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
  }

  .site-nav.is-open {
    display: flex;
  }

  .site-nav > a,
  .site-nav .nav-login {
    padding: 11px 12px;
    border-radius: 9px;
  }

  .site-nav > a:hover,
  .site-nav > a.is-active {
    background: var(--paper-warm);
  }

  .site-nav > a.is-active::after {
    display: none;
  }

  .site-nav .nav-login {
    margin-top: 4px;
    color: var(--paper);
    text-align: center;
  }

  .nav-account {
    justify-content: space-between;
    margin-top: 6px;
    padding: 10px 12px 2px;
    border-top: 1px solid var(--line);
    border-left: 0;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px 0;
  }

  .hero-stats div:nth-child(3) {
    padding-left: 0;
    border-left: 0;
  }

  .page-hero-inner {
    align-items: flex-start;
    flex-direction: column;
    gap: 22px;
  }

  .filters-card,
  .admin-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filters-card .filter-search,
  .admin-filters .filter-search,
  .filters-card .field:nth-of-type(4) {
    grid-column: 1 / -1;
  }

  .filter-actions {
    grid-column: 1 / -1;
  }

  .filters-card .filter-actions .button {
    flex: 1;
  }

  .detail-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 24px;
  }

  .detail-tracking {
    width: 100%;
    grid-template-columns: 1fr auto;
    align-items: center;
  }

  .detail-tracking strong {
    grid-column: 1;
  }

  .detail-tracking .button {
    grid-column: 2;
    grid-row: 1 / span 2;
    margin-top: 0;
  }

  .detail-sidebar {
    grid-template-columns: 1fr;
  }

  .form-section {
    padding: 29px 26px;
  }

  .form-footer {
    padding: 24px 26px;
  }

  .admin-update-grid {
    grid-template-columns: 1fr;
  }

  .admin-update-grid .field:last-child {
    grid-column: auto;
  }

  .admin-update-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-update-footer .button {
    width: 100%;
  }

  .footer-grid {
    grid-template-columns: 1.2fr 1fr 1fr;
  }
}

@media (max-width: 650px) {
  .container,
  .container.narrow {
    width: min(100% - 28px, var(--container));
  }

  h1 {
    font-size: clamp(2.2rem, 10vw, 3.2rem);
  }

  .section {
    padding: 60px 0;
  }

  .section-tight {
    padding-top: 32px;
  }

  .hero {
    padding: 50px 0 56px;
  }

  .hero-copy h1 {
    font-size: clamp(2.65rem, 13vw, 4rem);
  }

  .hero-lead {
    font-size: 0.98rem;
  }

  .hero-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .hero-actions .button {
    width: 100%;
  }

  .hero-stats {
    margin-top: 38px;
  }

  .tracker-card {
    padding: 25px;
  }

  .tracker-card::before {
    left: 25px;
    right: 25px;
  }

  .input-button-row {
    flex-direction: column;
  }

  .input-button-row .button {
    width: 100%;
  }

  .form-section {
    padding: 25px 20px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .severity-grid {
    grid-template-columns: 1fr;
  }

  .severity-card {
    min-height: 72px;
  }

  .form-footer {
    align-items: stretch;
    flex-direction: column;
    padding: 23px 20px;
  }

  .form-footer .button {
    width: 100%;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 14px;
  }

  .report-grid {
    grid-template-columns: 1fr;
  }

  .filters-card,
  .admin-filters {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .filters-card .filter-search,
  .admin-filters .filter-search,
  .filters-card .field:nth-of-type(4),
  .filter-actions {
    grid-column: auto;
  }

  .filter-actions {
    flex-direction: column;
  }

  .results-bar {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .pagination {
    gap: 8px;
  }

  .pagination-link {
    padding-inline: 12px;
    font-size: 0.76rem;
  }

  .pagination-status {
    font-size: 0.72rem;
  }

  .detail-hero {
    padding-top: 28px;
  }

  .detail-heading h1 {
    font-size: clamp(2rem, 10vw, 2.9rem);
  }

  .detail-card,
  .status-card {
    padding: 23px;
  }

  .detail-facts {
    grid-template-columns: 1fr;
  }

  .detail-actions {
    flex-direction: column;
  }

  .detail-actions .button {
    width: 100%;
  }

  .confirmation-card {
    padding: 28px 18px;
  }

  .tracking-box {
    align-items: flex-start;
    flex-direction: column;
  }

  .tracking-box .button {
    width: 100%;
  }

  .confirmation-summary {
    grid-template-columns: 1fr;
  }

  .confirmation-actions {
    flex-direction: column;
  }

  .confirmation-actions .button {
    width: 100%;
  }

  .next-steps {
    padding-inline: 0;
  }

  .next-steps-list {
    grid-template-columns: 1fr;
  }

  .dashboard-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .dashboard-user {
    align-self: flex-start;
  }

  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stat-card {
    gap: 10px;
    padding: 13px;
  }

  .stat-icon {
    width: 38px;
    height: 38px;
  }

  .stat-card strong {
    font-size: 1.3rem;
  }

  .admin-report-top {
    grid-template-columns: 76px minmax(0, 1fr);
    gap: 14px;
    padding: 15px;
  }

  .admin-thumb {
    width: 76px;
  }

  .admin-report-links {
    grid-column: 1 / -1;
  }

  .admin-update summary {
    align-items: flex-start;
    padding: 12px 15px;
  }

  .summary-hint {
    display: none;
  }

  .admin-update form {
    padding: 0 15px 15px;
  }

  .admin-update-grid {
    padding: 13px;
  }

  .footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: 30px;
  }

  .footer-brand {
    grid-column: 1 / -1;
  }

  .footer-bottom {
    align-items: flex-start;
    flex-direction: column;
    gap: 7px;
  }
}

@media (max-width: 390px) {
  .hero-stats {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .hero-stats div {
    padding: 0;
    border-left: 0;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }

  .detail-tracking {
    grid-template-columns: 1fr;
  }

  .detail-tracking .button {
    grid-column: 1;
    grid-row: auto;
    margin-top: 7px;
  }

  .pagination-status {
    display: none;
  }
}

/* --------------------------------------------------------------------------
   Account security and sign-in extras
   -------------------------------------------------------------------------- */

.nav-user {
  text-decoration: none;
  border-radius: 999px;
}

.nav-user:hover,
.nav-user:focus-visible {
  color: var(--ink);
}

.auth-inline-link {
  font-size: 0.78rem;
  font-weight: 650;
}

.auth-divider {
  position: relative;
  margin: 20px 0 16px;
  text-align: center;
}

.auth-divider::before {
  content: "";
  position: absolute;
  top: 50%;
  right: 0;
  left: 0;
  height: 1px;
  background: var(--line);
}

.auth-divider span {
  position: relative;
  padding: 0 12px;
  color: var(--muted);
  background: var(--paper);
  font-size: 0.74rem;
  font-weight: 650;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.button-google {
  color: var(--ink);
  background: var(--paper);
  border-color: var(--line-strong);
}

.button-google:hover {
  background: var(--paper-soft);
  border-color: #aeb9a9;
}

.google-icon {
  flex: none;
}

.auth-fineprint {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 0.74rem;
  line-height: 1.5;
  text-align: center;
}

.account-section {
  padding-block: 54px 70px;
}

.account-shell {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1000px;
}

.account-heading {
  max-width: 700px;
}

.account-heading h1 {
  margin-bottom: 10px;
  font-size: clamp(2rem, 4vw, 2.8rem);
}

.account-heading > p:not(.eyebrow) {
  margin: 0;
  color: var(--muted);
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
  align-items: start;
}

.account-card {
  padding: 28px;
}

.account-card h2 {
  margin-bottom: 6px;
  font-size: 1.35rem;
}

.account-subtitle {
  margin: 0 0 18px;
  color: var(--muted);
  font-size: 0.86rem;
}

.account-meta {
  display: grid;
  gap: 11px;
  margin: 0 0 22px;
  padding: 15px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.account-meta div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.account-meta dt {
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.account-meta dd {
  margin: 0;
  font-weight: 650;
  text-align: right;
}

.account-card .field {
  margin-bottom: 16px;
}

.account-card-wide {
  width: 100%;
}

.account-setup {
  display: grid;
  gap: 7px;
  margin: 12px 0;
  padding-left: 20px;
  color: var(--muted);
  font-size: 0.84rem;
}

.account-setup code,
.account-note code {
  padding: 2px 5px;
  background: var(--paper-warm);
  border-radius: 5px;
  font-family: var(--font-mono);
  font-size: 0.76rem;
  overflow-wrap: anywhere;
}

.account-note {
  margin: 0;
  color: var(--muted);
  font-size: 0.82rem;
}

.account-back {
  margin: 0;
}

.field-help {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 0.76rem;
}

.field-feedback {
  margin: 7px 0 0;
  color: var(--red);
  font-size: 0.78rem;
  font-weight: 650;
}

.password-meter {
  height: 6px;
  margin-top: 9px;
  overflow: hidden;
  background: var(--line);
  border-radius: 999px;
}

.password-meter span {
  display: block;
  width: 0;
  height: 100%;
  background: var(--red);
  border-radius: inherit;
  transition: width 0.2s ease, background 0.2s ease;
}

.password-meter span.is-medium {
  background: var(--amber-deep);
}

.password-meter span.is-strong {
  background: var(--green);
}

.password-rules {
  display: grid;
  gap: 5px;
  margin: 10px 0 0;
  padding: 0;
  color: var(--muted);
  font-size: 0.76rem;
  list-style: none;
}

.password-rules li {
  position: relative;
  padding-left: 19px;
}

.password-rules li::before {
  content: "○";
  position: absolute;
  left: 0;
  color: var(--line-strong);
}

.password-rules li.is-met {
  color: var(--green);
}

.password-rules li.is-met::before {
  content: "✓";
  color: var(--green);
  font-weight: 700;
}

.reset-link-box {
  margin: 18px 0;
  padding: 16px;
  background: var(--paper-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
}

.reset-link-box label {
  display: block;
  color: var(--muted);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.reset-link-box input {
  margin: 7px 0 11px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
}

.reset-link-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 900px) {
  .account-grid {
    grid-template-columns: 1fr;
  }

  .account-card {
    padding: 24px;
  }
}

@media (max-width: 560px) {
  .label-row {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 4px;
  }

  .account-meta div {
    flex-direction: column;
    gap: 2px;
  }

  .account-meta dd {
    text-align: left;
  }

  .reset-link-actions .button {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
````

### File: static/js/app.js

````javascript
(() => {
  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.getElementById("site-nav");

  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
      navToggle.classList.toggle("is-open", isOpen);
    });

    nav.addEventListener("click", (event) => {
      if (event.target.closest("a") && window.innerWidth <= 820) {
        nav.classList.remove("is-open");
        navToggle.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll("[data-dismiss-flash]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.getAttribute("data-copy");
      if (!value) return;

      try {
        await navigator.clipboard.writeText(value);
      } catch {
        const helper = document.createElement("textarea");
        helper.value = value;
        helper.setAttribute("readonly", "");
        helper.style.position = "fixed";
        helper.style.opacity = "0";
        document.body.appendChild(helper);
        helper.select();
        document.execCommand("copy");
        helper.remove();
      }

      const original = button.textContent;
      button.textContent = "Copied";
      button.classList.add("is-copied");
      window.setTimeout(() => {
        button.textContent = original;
        button.classList.remove("is-copied");
      }, 1800);
    });
  });

  const fileInput = document.querySelector("[data-file-input]");
  const fileName = document.querySelector("[data-file-name]");
  if (fileInput && fileName) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      fileName.textContent = file ? file.name : "No photo selected";
      fileName.classList.toggle("has-file", Boolean(file));
    });
  }

  const description = document.getElementById("description");
  const descriptionCount = document.querySelector("[data-description-count]");
  if (description && descriptionCount) {
    const updateCount = () => {
      descriptionCount.textContent = `${description.value.length} / 3000`;
    };
    description.addEventListener("input", updateCount);
    updateCount();
  }

  const passwordChecks = [
    (value) => value.length >= 12,
    (value) => /[A-Z]/.test(value),
    (value) => /[a-z]/.test(value),
    (value) => /[0-9]/.test(value),
    (value) => /[^A-Za-z0-9]/.test(value),
  ];

  document.querySelectorAll("[data-password-form]").forEach((form) => {
    const input = form.querySelector("[data-password-input]");
    const confirm = form.querySelector("[data-password-confirm]");
    const meter = form.querySelector("[data-password-meter]");
    const matchNote = form.querySelector("[data-password-match]");
    const rules = Array.from(form.querySelectorAll("[data-password-rules] li"));
    if (!input) return;

    const updatePasswordHints = () => {
      const value = input.value;
      let met = 0;

      rules.forEach((rule, index) => {
        const check = passwordChecks[index];
        const passed = check ? check(value) : false;
        rule.classList.toggle("is-met", passed);
        if (passed) met += 1;
      });

      if (meter) {
        meter.style.width = `${Math.round((met / passwordChecks.length) * 100)}%`;
        meter.classList.toggle("is-medium", met >= 3 && met < passwordChecks.length);
        meter.classList.toggle("is-strong", met === passwordChecks.length);
      }

      if (confirm && matchNote) {
        const mismatch = confirm.value.length > 0 && confirm.value !== value;
        matchNote.hidden = !mismatch;
      }
    };

    input.addEventListener("input", updatePasswordHints);
    confirm?.addEventListener("input", updatePasswordHints);
    updatePasswordHints();
  });
})();
````

### File: static/images/roadwatch-logo.svg

````xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img">
  <rect width="64" height="64" rx="16" fill="#14231f"/>
  <path d="M23 49 27.5 15h9L41 49" fill="none" stroke="#f4f6f1" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M31 39h2M32 29h1" stroke="#f2b705" stroke-width="4" stroke-linecap="round"/>
  <circle cx="49" cy="15" r="6" fill="#f2b705"/>
</svg>
````
