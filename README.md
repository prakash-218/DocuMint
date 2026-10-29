# DocuMint

Quotations, proforma invoices, GST and export invoices for a small engineering business: grouped in
**projects**, with the customer's POs and drawings, synced **email threads**, and notifications for
owners and admins.

- Python 3.12, Flask 3, server-rendered Jinja pages
- PostgreSQL 16 through SQLAlchemy 2 (`store/`), migrations with Alembic (`alembic/`)
- Files in S3-compatible object storage (a Railway Bucket in production, a local folder otherwise)
- PDFs with xhtml2pdf; email sync over IMAP by a small worker
- Hosted on Railway: web service, cron worker, Postgres and a Bucket

## Run it locally

You need Python 3.11+ and Docker.

```bash
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

docker run -d --name documint-pg -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=documint -p 5434:5432 postgres:16-alpine
cp .env.example .env                                    # the defaults point at that container

python scripts/dbtool.py demo                           # create the tables and load the demo companies
flask --app wsgi run --debug                            # http://127.0.0.1:5000
```

`scripts/dbtool.py migrate` applies new migrations; `reset` wipes the database (it refuses on Railway
production). After changing `store/schema.py`, create a migration with
`alembic revision --autogenerate -m "what changed"` and review it.

### The React screens

New screens are React (TypeScript, built with Vite) in `frontend/`, placed inside the server-rendered
pages as islands: `{{ island('name', props) }}` (`templates/_macros.html`) renders a `<div data-island>`
that `frontend/src/main.tsx` mounts, using the component registered under that name in
`frontend/src/islands.ts`. They read and write through the JSON endpoints in `blueprints/api_bp.py`, with
the same login, organization and roles as the pages. You need Node 22 for this part.

```bash
cd frontend
npm ci                                                  # .npmrc works around an npm resolver bug
npm run watch                                           # rebuilds static/app on every change
npm test && npm run typecheck
```

Without a build the pages work as before, just without their React parts. Docker and CI build it
themselves (`static/app` isn't committed).

Demo logins (password `demo12345`): `michael.chen@techflow.com` (owner), `sarah.martinez@techflow.com`
(member), `david.kim@techflow.com` (viewer), `emily.rodriguez@nexus.com` (owner of the Nexus companies).

## Configuration

| Variable | What it does |
|---|---|
| `DATABASE_URL` | Postgres connection. Railway: `${{Postgres.DATABASE_URL}}` |
| `SECRET_KEY` | Signs sessions. Required in production (the app refuses to start without it) |
| `FLASK_ENV` | `production` on Railway (secure cookies, https links) |
| `S3_BUCKET`, `S3_ENDPOINT`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Bucket for uploaded and emailed files. Railway: reference the Bucket's `BUCKET`, `ENDPOINT`, `REGION`, `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`. Without them, files go to `STORAGE_DIR` (default `var/storage`) |
| `EMAIL_ACCOUNTS` | Mailboxes to sync, as prefixes, e.g. `INFO,SALES` |
| `<PREFIX>_IMAP_HOST`, `_PORT` (993), `_SSL` (1), `_USER`, `_PASSWORD`, `_FOLDERS` | One set per mailbox. `_FOLDERS` defaults to INBOX plus the server's Sent folder |
| `EMAIL_ORG_DOMAIN` | Which organization the mail belongs to (default: the mailbox's domain) |
| `EMAIL_SYNC_DAYS` | How far back the first sync reaches (default 90) |
| `LOG_FORMAT`, `LOG_LEVEL`, `SLOW_QUERY_MS` | JSON logs are on automatically on Railway; `SLOW_QUERY_MS=200` logs slow queries |

## How it works

### Projects

Every quotation, proforma and invoice belongs to a **project** (one customer, one piece of work, numbered
`PRJ-001`). New documents ask for a project first; converting or revising keeps the new document in its
project. A project also holds the customer's files (PO, drawings, specs), earlier documents made outside
DocuMint (uploaded as files), email threads and an activity feed. A PO uploaded with its number fills
"Buyer's order no. & date" on the project's drafts.

### Documents

| Type | Statuses | Typical number |
|---|---|---|
| Quotation | draft → sent → accepted / declined (or revised) → converted | `TF/Q/027/26-27` |
| Proforma invoice | draft → sent → converted | `PI 009(26-27)` |
| Invoice | draft → pending → paid | `037` |

An invoice made with an **export template** (foreign currency, "export" in the name, or set under the
template's Pages & printing) prints as an Export Invoice: LUT, shipping details, packing list. Numbering
restarts each financial year; formats and next numbers are under Settings → Business profile. With a
GSTIN set, documents pick CGST+SGST, IGST or LUT from the customer's address. Money is never added
across currencies. URLs follow the type: `/quotes/<id>`, `/proformas/<id>`, `/invoices/<id>`.

Templates are edited in a builder; a version that documents already use is never changed, saving makes
the next version.

### Email

The worker copies mail from each mailbox over IMAP (read-only: nothing is marked as read) and groups it
into threads by its reply headers, then by subject. A thread joins a project when its subject has the
project number (`PRJ-012`) or a document number (`TF/Q/027/26-27`), or when it's a reply in a linked
thread. The sender's domain (a customer's **Email domains**) picks the customer. Everything else waits
under **Emails → Not in a project**, where it can be linked by hand. Attachments are kept with the
message. Owners and admins are notified of customer mail on projects.

**Email** on a project or a sent document sends from the same mailbox (`mailsend.py`): to the project's
contacts (whoever gets everything, with Accounts copied on proformas and invoices), its documents
attached as PDFs, as a reply in one of the project's threads or as a new one with the project number in
the subject. A copy goes to the mailbox's Sent folder and the email shows on the project at once; replies
come back into the thread. It needs the mailbox on the web service too, plus its SMTP server:
`EMAIL_ACCOUNTS`, the mailbox's `*_IMAP_*` (Railway can reference the worker's), `INFO_SMTP_HOST`, and
`INFO_SMTP_PORT=465` (or `587` with `INFO_SMTP_SSL=0`); `EMAIL_SEND_FROM` picks the mailbox when there's
more than one. Through Gmail: `GMAIL_SMTP_HOST=smtp.gmail.com` (the same app password), and
`GMAIL_SMTP_FROM=info@...` when Gmail has that address under "Send mail as"; Gmail keeps the Sent copy
itself. Until `*_SMTP_HOST` is set, the form says sending isn't set up.

### Roles

| | Owner | Admin | Member | Viewer |
|---|:-:|:-:|:-:|:-:|
| Create, edit, send documents; record payments; projects; upload files | ✓ | ✓ | ✓ | |
| Read synced email | ✓ | ✓ | ✓ | |
| Customers, templates, business profile, audit log, delete drafts | ✓ | ✓ | | |
| Team: approve, deactivate, change roles (admins can't touch owners) | ✓ | ✓ | | |
| Organization name and address; make owners | ✓ | | | |
| Notifications | ✓ | ✓ | | |
| View everything else | ✓ | ✓ | ✓ | ✓ |

Customers can log in to the portal (`/customer/login`) to see and download their own sent documents.

## Tests

```bash
pytest                                                   # unit tests (no database)

docker exec documint-pg psql -U postgres -c "CREATE DATABASE documint_test"
docker run -d --name documint-mail -e GREENMAIL_OPTS="-Dgreenmail.setup.test.all -Dgreenmail.hostname=0.0.0.0 -Dgreenmail.auth.disabled" -p 3143:3143 -p 3025:3025 greenmail/standalone:2.0.1
docker run -d --name documint-s3 -e initialBuckets=documint -p 9010:9090 adobe/s3mock:3.11.0
DOCUMINT_INTEGRATION_DB=1 DATABASE_URL=postgresql+psycopg://postgres:dev@127.0.0.1:5434/documint_test pytest
```

Integration tests wipe and reload the test database (its name must contain `test`). The email and
bucket tests skip themselves when GreenMail or the S3 mock isn't running.

## Deploying on Railway

One project in one region (Singapore, `asia-southeast1`), with:

1. **Postgres** (Railway template).
2. **Bucket** for files.
3. **Web**: this repo, `railway.json` (Dockerfile build, migrations as the pre-deploy step, health check
   on `/healthz`). Variables: `DATABASE_URL`, `SECRET_KEY`, `FLASK_ENV=production`, the five `S3_*`
   references. Custom domain (e.g. `app.example.com`): add the CNAME record Railway shows at your DNS host.
4. **Worker**: same repo, config file `railway.worker.json` (cron every 5 minutes, `python worker.py --once`).
   Variables: `DATABASE_URL`, the `S3_*` references, `EMAIL_ACCOUNTS` and each mailbox's `*_IMAP_*`.

Monitoring: each service's Metrics tab (CPU, memory, network, HTTP status and latency) and the Log
Explorer. Logs are JSON, so you can filter, e.g. `@status:500`, `@path:/projects`, `@durationMs:>1000`,
`@event:email_sync_done`. `/healthz` reports the database and bucket.

## Project layout

```
app.py, wsgi.py           app factory and entry point
config.py                 settings per environment
db.py                     database access: runs operations from store/procs.py
store/schema.py           the PostgreSQL schema (source for Alembic)
store/procs.py            every database operation, one function each
alembic/                  migrations
storage.py                bucket / local file storage
documents.py, document_service.py, invoice_service.py, calculations.py, money.py
                          document types, numbering, conversion, totals, PDFs
projects.py               projects, files, grouping
emailsync.py, worker.py   IMAP sync and the background worker
activity.py               project events and notifications
observability.py          JSON logs, request logging, /healthz
blueprints/               routes (api_bp: JSON for the React screens)
templates/, static/       pages, CSS, JS
frontend/                 React screens (TypeScript), built into static/app; frontend_assets.py loads them
scripts/dbtool.py         migrate / reset / demo
tests/                    unit tests; tests/integration against real services
```
