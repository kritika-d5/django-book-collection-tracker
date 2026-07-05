# Deploying Athenaeum to Vercel + Neon + Cloudinary

Vercel runs the app as serverless functions, so the two pieces of *state* live
in managed services:

- **Neon** — Postgres database (Vercel can't run SQLite; the filesystem is read-only)
- **Cloudinary** — stores uploaded book/community covers (same reason)
- **Vercel** — runs Django and serves static files

The code already switches to these automatically when their environment variables
are present, and stays on local SQLite + local disk when they aren't.

---

## 1. Create the managed services

**Neon** (https://neon.tech): create a project, then copy the **pooled**
connection string (the host contains `-pooler`). It looks like:
```
postgresql://USER:PASSWORD@ep-xxx-pooler.REGION.aws.neon.tech/neondb?sslmode=require
```

**Cloudinary** (https://cloudinary.com): from the dashboard copy the
**API environment variable**:
```
cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

**Generate a Django secret key** locally:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 2. Seed the database + covers (run locally, pointed at the cloud)

You run these from your own machine with the cloud connection strings set, so
your data and covers land in Neon + Cloudinary before the first deploy. Pick the
option that fits. Examples use **Windows PowerShell** (macOS/Linux: swap
`$env:VAR="..."` for `export VAR="..."`).

### Option A — keep the exact data you already have

First dump your current local data **before** setting any cloud variables (so it
reads your local SQLite):

```powershell
python -X utf8 manage.py dumpdata --natural-primary --natural-foreign `
  -e contenttypes -e auth.permission -e sessions -e admin.logentry `
  --indent 2 -o seed.json
```

Then point at the cloud and load everything — rows into Neon, cover files into
Cloudinary:

```powershell
$env:DATABASE_URL="postgresql://...-pooler...sslmode=require"
$env:CLOUDINARY_URL="cloudinary://API_KEY:API_SECRET@CLOUD_NAME"

python manage.py migrate                     # build the schema in Neon
python manage.py loaddata seed.json          # restore your rows
python manage.py upload_media_to_cloudinary  # push your local covers to Cloudinary
```

`loaddata` restores the cover *paths*; `upload_media_to_cloudinary` uploads the
matching image *files* under those same names so they display. Run it with
`--dry-run` first to preview. Your dumped users come across too, so
`createsuperuser` is optional.

### Option B — start fresh from Open Library

Skip the dump entirely; import a new catalog (books **and** covers) straight into
the cloud:

```powershell
$env:DATABASE_URL="postgresql://...-pooler...sslmode=require"
$env:CLOUDINARY_URL="cloudinary://API_KEY:API_SECRET@CLOUD_NAME"

python manage.py migrate
python manage.py import_books fantasy "science fiction" romance --limit 12
python manage.py createsuperuser
```

## 3. Push to GitHub

```bash
git add .
git commit -m "Add Vercel + Neon + Cloudinary deployment config"
git push
```

## 4. Import the project into Vercel

1. At https://vercel.com → **Add New → Project** → import your GitHub repo.
2. Framework preset: **Other** (the included `vercel.json` handles the build).
3. Before deploying, add **Environment Variables** (Settings → Environment Variables):

   | Name | Value |
   |------|-------|
   | `DJANGO_SECRET_KEY` | the key from step 1 |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `.vercel.app` |
   | `DATABASE_URL` | your Neon pooled URL |
   | `CLOUDINARY_URL` | your Cloudinary URL |

4. Click **Deploy**. When it finishes, open the `*.vercel.app` URL.

> Using a custom domain later? Add it to `DJANGO_ALLOWED_HOSTS` (comma-separated,
> e.g. `.vercel.app,athenaeum.com`) and redeploy — CSRF origins update automatically.

## How it fits together

- `vercel.json` — one build runs `book_tracker_project/wsgi.py` as the Python
  serverless app; another runs `build_files.sh` (installs deps, `collectstatic`)
  and serves `/static/*` from `staticfiles/`.
- `wsgi.py` exposes `app` for Vercel's Python runtime.
- Static files: WhiteNoise (compressed) as a fallback; Vercel serves `/static/`
  directly via the route.

## Updating the site

Just `git push` — Vercel redeploys automatically. If you changed models, run
`python manage.py migrate` locally with `DATABASE_URL` set (Vercel's build does
not run migrations).

## Notes

- **Migrations run from your machine**, not from Vercel's build — that's why
  step 2 runs `migrate` locally against Neon.
- **Serverless connections:** the code uses `conn_max_age=0` and you're using
  Neon's pooled endpoint, which is built for serverless — no extra tuning needed.
- **Optional hardening env vars:** `DJANGO_SSL_REDIRECT=False` to disable the
  HTTP→HTTPS redirect (Vercel already serves HTTPS), `DJANGO_HSTS_SECONDS=31536000`
  to enable HSTS once you're confident the site is HTTPS-only.
- **Alternative host:** PythonAnywhere keeps SQLite + local media with no external
  services, if you ever want a simpler (non-serverless) option.
