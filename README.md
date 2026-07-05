# Athenaeum

A personal book tracker with a "living bookshelf" aesthetic — a dark-academia
reading room where you shelve books, write reviews, and join reader circles.
Built with Django.

## Features

- **Three shelves** — file any book under *Want to Read*, *Currently Reading*,
  or *Read*, with a drag-the-ribbon interaction on each book's page.
- **Reviews & ratings** — rate read books 1–5 and leave reviews; readers can
  comment and reply on each other's reviews.
- **Discover** — browse the catalog by genre or author, or search by title/author.
- **Communities** — create reader circles, post discussions, and link posts to
  books; book pages surface how many members of your communities have shelved a title.
- **Rich covers** — books carry cover art, imported automatically from Open Library.
- **REST API** — read-only endpoints for books, authors, and genres under `/api/v1/`.

## Tech stack

- **Django 5.2** (Python 3.11) with Django REST Framework
- **SQLite** for storage, **Pillow** for cover images
- Server-rendered templates + vanilla JS; **WhiteNoise** for static files
- Fonts: Fraunces (display), Inter (body), JetBrains Mono (metadata)

## Getting started

```bash
git clone https://github.com/YOURUSER/book_tracker_project.git
cd book_tracker_project

python -m venv venv
venv\Scripts\activate        # Windows;  use: source venv/bin/activate  on macOS/Linux
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000.

### Seed the catalog

Import books and covers from the free Open Library API by subject:

```bash
python manage.py import_books fantasy "science fiction" romance --limit 12
```

Use `--no-covers` to skip image downloads or `--dry-run` to preview.

## Project structure

| App | Responsibility |
|-----|----------------|
| `core` | Pages, auth, search, dashboard ("My Shelves"), and the landing room |
| `books` | `Book` / `Author` / `Genre` models, the REST API, and the import command |
| `shelves` | `UserShelf` (shelf status, rating, review) and review comments |
| `communities` | `Community`, memberships, and discussion posts |

## Deployment

The project reads secrets from the environment and hardens itself when
`DEBUG=False`. It runs on local SQLite + disk by default, and switches to
Postgres and Cloudinary automatically when their URLs are set. See
[DEPLOY.md](DEPLOY.md) for a step-by-step guide to hosting it on
**Vercel + Neon + Cloudinary**.

## Configuration

Set these environment variables in production (all have dev-friendly defaults):

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames (e.g. `.vercel.app`) |
| `DATABASE_URL` | Postgres URL (e.g. Neon); falls back to SQLite |
| `CLOUDINARY_URL` | Cloudinary URL for uploaded covers; falls back to local disk |
| `DJANGO_SSL_REDIRECT` | Optional; `False` to disable HTTP→HTTPS redirect |
| `DJANGO_HSTS_SECONDS` | Optional; enable HSTS once HTTPS-only |
