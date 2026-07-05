"""
Upload local media files to the configured default storage (e.g. Cloudinary).

Use this after `loaddata` when moving to a host that stores media in the cloud:
`loaddata` restores the rows (including cover paths), and this command pushes the
matching image files from your local `media/` folder up to Cloudinary under the
same names, so `cover_image.url` resolves on the live site.

Run it locally with DATABASE_URL and CLOUDINARY_URL pointing at your cloud services:
    python manage.py upload_media_to_cloudinary --dry-run
    python manage.py upload_media_to_cloudinary
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = 'Upload local media files to the default storage (e.g. Cloudinary).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-media',
            default=str(Path(settings.BASE_DIR) / 'media'),
            help='Folder holding the local media files (default: <project>/media).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List what would be uploaded without contacting the storage.',
        )

    def handle(self, *args, **options):
        local_root = Path(options['local_media'])
        dry_run = options['dry_run']
        uploaded = skipped = missing = 0

        for model in apps.get_models():
            file_fields = [
                f.name for f in model._meta.get_fields()
                if isinstance(f, models.FileField)
            ]
            if not file_fields:
                continue

            for obj in model.objects.all():
                for field_name in file_fields:
                    field_file = getattr(obj, field_name)
                    if not field_file:
                        continue

                    name = field_file.name
                    local_path = local_root / name

                    if not local_path.exists():
                        self.stderr.write(self.style.WARNING(f'  missing local file: {name}'))
                        missing += 1
                        continue

                    if dry_run:
                        self.stdout.write(f'  would upload: {name}')
                        uploaded += 1
                        continue

                    if default_storage.exists(name):
                        skipped += 1
                        continue

                    with open(local_path, 'rb') as fh:
                        saved_name = default_storage.save(name, File(fh))

                    # If the storage renamed the file, keep the DB in sync.
                    if saved_name != name:
                        setattr(obj, field_name, saved_name)
                        obj.save(update_fields=[field_name])

                    self.stdout.write(self.style.SUCCESS(f'  uploaded: {name}'))
                    uploaded += 1

        verb = 'Would upload' if dry_run else 'Uploaded'
        self.stdout.write(self.style.SUCCESS(
            f'\n{verb} {uploaded} file(s); skipped {skipped} already present; '
            f'{missing} missing locally.'
        ))
