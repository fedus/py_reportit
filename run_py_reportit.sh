#!/bin/bash
set -euo pipefail

if [ -v MIGRATE ]; then
    alembic upgrade head
fi

exec python3 -m py_reportit.crawler.py_reportit
