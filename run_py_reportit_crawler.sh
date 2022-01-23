#!/bin/bash
set -euo pipefail

if [ -v MIGRATE ]; then
    alembic upgrade head
fi

exec celery -A py_reportit.crawler.py_reportit:celery_app worker -B loglevel=INFO
