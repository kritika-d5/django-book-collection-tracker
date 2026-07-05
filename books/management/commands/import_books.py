"""
Import books from the Open Library API by subject/genre.

Open Library is free and needs no API key. This command pulls popular works
for each subject you name, creates Author/Genre/Book rows, and downloads the
cover image into MEDIA_ROOT/book_covers/.

Examples:
    python manage.py import_books fantasy
    python manage.py import_books "science fiction" romance --limit 20
    python manage.py import_books history --no-covers
    python manage.py import_books fantasy --dry-run
"""
import json
import time
import urllib.parse
import urllib.request
from io import BytesIO

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from books.models import Author, Book, Genre

USER_AGENT = 'book-tracker-project/1.0 (educational project)'
SUBJECTS_URL = 'https://openlibrary.org/subjects/{subject}.json?limit={limit}'
WORK_URL = 'https://openlibrary.org/works/{work_id}.json'
COVER_URL = 'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg'


def _fetch_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def _fetch_bytes(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _extract_description(work_data):
    """Open Library stores description as a string or a {'value': ...} dict."""
    description = work_data.get('description')
    if isinstance(description, dict):
        return description.get('value', '')
    return description or ''


class Command(BaseCommand):
    help = 'Import books from the Open Library API by subject/genre.'

    def add_arguments(self, parser):
        parser.add_argument(
            'subjects',
            nargs='+',
            help='One or more subjects/genres to import, e.g. fantasy "science fiction".',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of books to import per subject (default: 10).',
        )
        parser.add_argument(
            '--no-covers',
            action='store_true',
            help='Skip downloading cover images (faster).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without writing to the database.',
        )

    def handle(self, *args, **options):
        subjects = options['subjects']
        limit = options['limit']
        download_covers = not options['no_covers']
        dry_run = options['dry_run']

        if limit < 1:
            raise CommandError('--limit must be a positive integer.')

        created_count = 0
        skipped_count = 0

        for subject in subjects:
            slug = subject.strip().lower().replace(' ', '_')
            self.stdout.write(self.style.MIGRATE_HEADING(f'\nSubject: {subject}'))

            try:
                data = _fetch_json(SUBJECTS_URL.format(
                    subject=urllib.parse.quote(slug), limit=limit,
                ))
            except Exception as exc:  # noqa: BLE001 - surface any network/parse error
                self.stderr.write(self.style.ERROR(f'  Failed to fetch subject "{subject}": {exc}'))
                continue

            works = data.get('works', [])
            if not works:
                self.stdout.write(self.style.WARNING(f'  No works found for "{subject}".'))
                continue

            genre = None
            if not dry_run:
                genre, _ = Genre.objects.get_or_create(name=subject.strip().title())

            for work in works:
                title = (work.get('title') or '').strip()
                if not title:
                    continue

                author_names = [
                    a.get('name', '').strip()
                    for a in work.get('authors', [])
                    if a.get('name')
                ]

                if Book.objects.filter(title__iexact=title).exists():
                    self.stdout.write(f'  - skip (exists): {title}')
                    skipped_count += 1
                    continue

                if dry_run:
                    authors_display = ', '.join(author_names) or 'Unknown'
                    self.stdout.write(f'  + would add: {title} - {authors_display}')
                    created_count += 1
                    continue

                # Fetch the work detail for a description (subject endpoint omits it).
                description = ''
                work_key = work.get('key', '')  # e.g. "/works/OL12345W"
                if work_key.startswith('/works/'):
                    work_id = work_key.split('/works/')[1]
                    try:
                        work_data = _fetch_json(WORK_URL.format(work_id=work_id))
                        description = _extract_description(work_data)
                    except Exception:  # noqa: BLE001 - description is optional
                        description = ''
                    time.sleep(0.2)  # be gentle with the public API

                book = Book.objects.create(title=title, description=description)

                for name in author_names:
                    author, _ = Author.objects.get_or_create(name=name)
                    book.authors.add(author)

                book.genres.add(genre)

                cover_id = work.get('cover_id')
                if download_covers and cover_id:
                    try:
                        image_bytes = _fetch_bytes(COVER_URL.format(cover_id=cover_id))
                        filename = f'{cover_id}.jpg'
                        book.cover_image.save(filename, File(BytesIO(image_bytes)), save=True)
                    except Exception as exc:  # noqa: BLE001 - cover is optional
                        self.stderr.write(self.style.WARNING(
                            f'    cover failed for "{title}": {exc}'
                        ))
                    time.sleep(0.2)

                authors_display = ', '.join(author_names) or 'Unknown'
                self.stdout.write(self.style.SUCCESS(f'  + added: {title} - {authors_display}'))
                created_count += 1

        verb = 'Would add' if dry_run else 'Added'
        self.stdout.write(self.style.SUCCESS(
            f'\n{verb} {created_count} book(s); skipped {skipped_count} existing.'
        ))
