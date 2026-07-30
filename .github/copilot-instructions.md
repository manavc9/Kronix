# Project Guidelines

## Code Style
Python Flask application with SQLAlchemy ORM. Follow PEP 8 conventions. Reference [app/models.py](app/models.py) and [app/routes.py](app/routes.py) for code patterns.

## Architecture
Flask app with single Blueprint, SQLAlchemy models for Car, WorkOrder, and related entities. SQLite database with soft-deletion and activity logging. Three locations (Lachine, Sarnia, Raymond) with role-based access.

Major components: Authentication (session-based), Dashboards, Car Management, Shop Floor, Yard, Cleaning, Scheduling.

## Build and Test
Run: `python run.py` (starts Flask on localhost:5000 with debug=True)

Database: SQLite auto-created and seeded on startup.

No test framework currently implemented.

## Conventions
- Soft-deletion: Use `is_active=False` or `cleared_at` instead of hard deletes.
- Activity logging: Log all changes via `ActivityLog` model.
- Status ownership: Pre-repair → Customer Service, Repair → Scheduler, Post-repair → Customer Service.
- Returning cars: Increment `visit_number` on same Car record.
- Location scoping: Filter by `location_id` for non-admin roles.

Reference [app/__init__.py](app/__init__.py) for app factory and seed data patterns.