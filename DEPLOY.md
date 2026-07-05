# Deploying Athenaeum to PythonAnywhere (free tier)

This app is production-ready: settings read secrets from the environment, static
files are collected to `staticfiles/`, and HTTPS hardening turns on automatically
when `DEBUG=False`. Follow these steps once and you'll have a live site at
`https://YOURNAME.pythonanywhere.com`.

Replace **`YOURNAME`** everywhere below with your PythonAnywhere username.

---

## 1. Push your code to GitHub

From your project folder locally:

```bash
git add .
git commit -m "Prep for deployment"
git push
```

> Your `.gitignore` deliberately excludes `db.sqlite3`, `media/`, and `.env`, so
> the server starts with an **empty database and no cover images**. Step 7 seeds them.

## 2. Generate a production secret key

Run this locally and copy the output — you'll paste it in step 5:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 3. Create the PythonAnywhere account + virtualenv

1. Sign up (free "Beginner" plan) at https://www.pythonanywhere.com.
2. Open a **Bash console** (Consoles tab) and clone your repo:
   ```bash
   git clone https://github.com/YOURUSER/book_tracker_project.git
   cd book_tracker_project
   ```
3. Create a virtualenv and install dependencies:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.11 athenaeum-venv
   pip install -r requirements.txt
   ```
   (The prompt now shows `(athenaeum-venv)`. To return to it later:
   `workon athenaeum-venv`.)

## 4. Create the web app (manual configuration)

1. **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.11**.
2. In the web app config page, set:
   - **Source code:** `/home/YOURNAME/book_tracker_project`
   - **Virtualenv:** `/home/YOURNAME/.virtualenvs/athenaeum-venv`

## 5. Configure the WSGI file (this is where env vars go)

On the Web tab, click the **WSGI configuration file** link
(`/var/www/YOURNAME_pythonanywhere_com_wsgi.py`). Delete everything in it and
replace with:

```python
import os
import sys

path = '/home/YOURNAME/book_tracker_project'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'book_tracker_project.settings'
os.environ['DJANGO_SECRET_KEY'] = 'PASTE-THE-KEY-FROM-STEP-2'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'YOURNAME.pythonanywhere.com'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Save it.

## 6. Add static & media file mappings

Still on the Web tab, scroll to **Static files** and add two rows:

| URL | Directory |
|--------|-----------|
| `/static/` | `/home/YOURNAME/book_tracker_project/staticfiles` |
| `/media/`  | `/home/YOURNAME/book_tracker_project/media` |

(WhiteNoise also serves `/static/` as a fallback, but this mapping is faster
because PythonAnywhere's web server handles it directly.)

## 7. Migrate, collect static, seed data

Back in the Bash console (with `(athenaeum-venv)` active, inside the project folder):

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Now fill the catalog. **Pick one:**

**Option A — import fresh from Open Library (try this first):**
```bash
python manage.py import_books fantasy "science fiction" romance --limit 12
```
This downloads books *and* covers server-side. It only works if Open Library is
on PythonAnywhere's free-tier allowlist — if it fails with a connection error,
use Option B.

**Option B — copy the data you already have (always works):**
1. Locally, dump your current data. The `-X utf8` flag is required on Windows so
   accented names (é, ö, …) don't crash the export:
   ```bash
   python -X utf8 manage.py dumpdata --natural-primary --natural-foreign \
     -e contenttypes -e auth.permission -e sessions -e admin.logentry \
     --indent 2 -o seed.json
   ```
2. Upload `seed.json` **and** your local `media/` folder to
   `/home/YOURNAME/book_tracker_project/` using the PythonAnywhere **Files** tab
   (or `git`/zip them across).
3. On the server:
   ```bash
   python manage.py loaddata seed.json
   ```

## 8. Reload and visit

Click the big green **Reload** button on the Web tab, then open
`https://YOURNAME.pythonanywhere.com`. Done.

---

## Updating the site later

```bash
workon athenaeum-venv
cd ~/book_tracker_project
git pull
pip install -r requirements.txt        # only if dependencies changed
python manage.py migrate               # only if models changed
python manage.py collectstatic --noinput   # only if static/ changed
```
Then hit **Reload** on the Web tab.

## Good to know

- **Keep it alive:** free apps are disabled after 3 months unless you click a
  "run until 3 months from now" button on the Web tab (you'll get an email).
- **Environment variables** all live in the WSGI file (step 5). Optional extras:
  - `DJANGO_SSL_REDIRECT=False` — disable the automatic HTTP→HTTPS redirect.
  - `DJANGO_HSTS_SECONDS=31536000` — enable HSTS once you're sure the site is
    HTTPS-only (leave unset while testing).
- **Whitelist:** on the free tier, server-side calls to the internet only reach
  allowlisted sites. This does **not** affect your design (fonts/images load in
  the visitor's browser) — only server-side fetches like `import_books`.
