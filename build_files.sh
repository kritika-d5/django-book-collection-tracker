#!/bin/bash
# Vercel build step: install dependencies and collect static files.
# Django's WSGI app is served separately by the @vercel/python build.
pip install -r requirements.txt
python manage.py collectstatic --noinput
