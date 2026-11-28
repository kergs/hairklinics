#!/usr/bin/env bash
# Runs on every deploy. Everything here is safe to repeat.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_services
python manage.py seed_schedule
python manage.py ensure_admin