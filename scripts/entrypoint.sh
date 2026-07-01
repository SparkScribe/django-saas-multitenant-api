#!/bin/bash
set -euo pipefail

echo "Waiting for PostgreSQL..."
while ! python -c "
import os, sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', 'django_saas_multitenant'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
    )
    conn.close()
except psycopg2.OperationalError:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

exec "$@"
