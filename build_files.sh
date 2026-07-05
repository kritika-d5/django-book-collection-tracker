#!/bin/bash
# Vercel build step: install dependencies and collect static files.
# Django's WSGI app is served separately by the @vercel/python build.
# --break-system-packages: Vercel's build image manages Python with uv, which
# blocks pip under PEP 668; this override is safe in the ephemeral build env.
python3 -m pip install --break-system-packages -r requirements.txt
python3 manage.py collectstatic --noinput
