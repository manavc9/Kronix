#!/usr/bin/env python3
"""
seed_demo_data.py — thin wrapper for local manual use.

The full demo dataset is now seeded automatically on first startup
via app/demo_seed.py.  Run this script only if you want to re-seed
an existing database after a manual reset (e.g. after deleting railops.db
and running python run.py to recreate the schema).

Usage:  python seed_demo_data.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.demo_seed import run

app = create_app()

with app.app_context():
    seeded = run(print_summary=True)
    if not seeded:
        print('Nothing to do — run.py already seeded the full dataset on startup.')
        print('To reset: delete instance/railops.db, then run python run.py.')
        sys.exit(0)
