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

DocuMint's screens are a single-page app: React (TypeScript, built with Vite, React Router) in `frontend/`. The app
(`frontend/src/app/`) draws the whole page (sidebar, header and screen) and moves between its screens without loading
a page; `frontend/src/app/routes.tsx` lists them. Flask still checks access for each address, then sends one page
(`templates/spa.html`, `nav.spa()`) with what the app starts with (`nav.boot()`: who's signed in and their permissions, the
sidebar for them, the page's messages). A form still posts to its Flask route; when that doesn't save,
`nav.spa(posted=True)` sends the app back with what was typed.

Two smaller parts load from the same build (`frontend/src/main.tsx` starts the one its page has a root for):

- `frontend/src/public/`: the pages outside the app (logging in, registering, choosing, making or joining an
  organization, the customer portal's login). The route decides the screen and its data as before, and
  `nav.public()` sends `templates/public.html`, the sign-in frame with the page's messages; React draws the form.
- `frontend/src/portal/`: the customer portal, its own small app over `/customer/api/documents`
  (`portal_view.py`), sent as `templates/portal.html` by `nav.portal()`.

PDFs and the error pages are still drawn on the server.

Dropdowns and pickers use [Mantine](https://mantine.dev) (`frontend/src/mantine/`), themed with the app's colours,
greys and IBM Plex and following its light/dark toggle. Only the styles of the components used are loaded; Mantine's
`baseline.css` is left out because `main.css` draws the page. Every dropdown is `frontend/src/mantine/Dropdown.tsx`
(Mantine's Select, posting through a hidden input in the app's forms); use it rather than a `<select>`. Tests render
through `frontend/src/test/render.tsx`, whose `pick()` chooses in a dropdown.

The screens read and write through the JSON endpoints in `blueprints/api_bp.py`, with the same login,
organization and permissions as the pages. You need Node 22 for this part.

```bash
cd frontend
npm ci                                                  # .npmrc works around an npm resolver bug
npm run watch                                           # rebuilds static/app on every change
npm test && npm run typecheck
```

Without a build the pages have no screens: run `npm run build` (or `watch`) first. Docker and CI build it
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

### Roles and permissions

Every check asks for a permission, never a role (`permissions.py`). Permissions are `<area>.<action>`:
documents by type (`quotes`, `proformas`, `invoices`, each `.read`, `.write`, `.delete`), then `projects.*`,
`files.*`, `customers.*`, `emails.*`, `costings.*`, `templates.*`, `team.*` and the rest. `GET /api/me` lists
someone's. The built-in roles are sets of them:

| | Owner | Admin | Member | Sales | Viewer |
|---|:-:|:-:|:-:|:-:|:-:|
| See quotations, projects, files and customers | ✓ | ✓ | ✓ | ✓ | ✓ |
| See proformas, invoices, what's owed and templates | ✓ | ✓ | ✓ | | ✓ |
| Make, edit and send quotations; projects and their files; contacts | ✓ | ✓ | ✓ | ✓ | |
| Make, edit and send proformas and invoices; record payments | ✓ | ✓ | ✓ | | |
| Read synced email | ✓ | ✓ | ✓ | | |
| Add and edit customers; delete draft quotations; delete projects | ✓ | ✓ | | ✓ | |
| Delete other drafts and sent documents; archive and delete customers; portal logins | ✓ | ✓ | | | |
| Costings, templates, business profile, audit log, notifications, syncing mail | ✓ | ✓ | | | |
| Team: approve, deactivate, change roles (admins can't touch owners) | ✓ | ✓ | | | |
| Organization name and address; make owners | ✓ | | | | |

An organization can also make **roles of its own** under Settings → Roles (`org_role`; a member with one has
role `custom` and its `role_id`). A role is any set of permissions except the two only owners have (the name and
address, and making owners), plus what each needs (making quotations needs seeing them). Nobody gives a role, or
changes the role of someone, beyond their own permissions, so an admin can't make an owner. Changing a role changes
what everyone with it may do on their next request. A role can't be deleted while someone has it. The roles API is
`/api/settings/roles`: GET lists them; POST `{name, description, permissions}` makes one; PATCH and DELETE
`/api/settings/roles/<id>` change or delete one.

`permissions.ENDPOINTS` says what each page and API endpoint needs, and `auth.require_org` checks it before
the view runs; an endpoint that isn't listed is refused, so a new page stays closed until it's added there
(`tests/test_permissions.py` fails until it is). A request about a document also needs reading that
document's type. The views then show only what someone may do (`permissions.can`, `can_doc`, `may_delete`).

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
3. **Web**: this repo, set up by `.railway/railway.ts` (Dockerfile build, migrations as the pre-deploy step,
   health check on `/healthz`), applied with `railway config apply` (see `.railway/README.md`). Variables:
   `DATABASE_URL`, `SECRET_KEY`, `FLASK_ENV=production`, the five `S3_*` references. Custom domain (e.g.
   `app.example.com`): add the CNAME record Railway shows at your DNS host.
4. **Worker**: same repo, set in its Railway settings (cron every 5 minutes, start command `python worker.py --once`).
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
nav.py                    the sidebar, the New menu and the React app's page (spa) and boot data
document_page.py          a document's page for the React app (GET /api/document/<id>)
editor_page.py            the new-document steps and the editor for the React app (GET /api/editor/...)
packing_page.py           a document's packing, box by box, for the React app (GET /api/packing/<id>)
customer_view.py, email_view.py, notifications_view.py, settings_view.py, costing_view.py, template_view.py,
portal_view.py
                          the other screens' JSON (GET /api/customers, /api/emails, /api/settings, /api/costings,
                          /api/templates..., and the portal's /customer/api/documents)
observability.py          JSON logs, request logging, /healthz
blueprints/               routes (api_bp: JSON for the React screens)
templates/, static/       the app's pages (spa, public, portal), PDFs, error pages, CSS, JS
frontend/                 the React app and screens (TypeScript), built into static/app; frontend_assets.py loads them
scripts/dbtool.py         migrate / reset / demo
tests/                    unit tests; tests/integration against real services
```
