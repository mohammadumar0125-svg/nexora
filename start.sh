#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================================="
echo " Starting NEXORA — The Next Generation Business Developer"
echo " Unified Public Site + Multi-Tenant Enterprise SaaS Application"
echo "=================================================================="

source "$DIR/venv/bin/activate"
export PYTHONPATH="$DIR/backend"
PORT="${PORT:-8000}"

python3 backend/scripts/setup_postgres.py
python3 backend/app/seed_enterprise.py

echo "Starting unified server on http://127.0.0.1:$PORT..."
exec python3 backend/run.py
