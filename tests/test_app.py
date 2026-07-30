"""
tests/test_app.py
-----------------
Basic integration tests for the Kronix Flask application.
Run with: pytest tests/
"""

import os
import pytest

# Force test environment before importing the app
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['WTF_CSRF_ENABLED'] = 'False'  # disable CSRF for tests


@pytest.fixture(scope='session')
def app():
    """Create application with in-memory SQLite database."""
    from app import create_app
    application = create_app()
    application.config['TESTING'] = True
    application.config['WTF_CSRF_ENABLED'] = False
    yield application


@pytest.fixture(scope='session')
def client(app):
    """Test client for the application."""
    return app.test_client()


@pytest.fixture(scope='session')
def db_session(app):
    """Database session bound to the test app context."""
    from app.models import db
    with app.app_context():
        yield db


# ── 1. App factory ────────────────────────────────────────────────────────────

def test_app_factory_creates_app(app):
    """App factory returns a Flask application."""
    from flask import Flask
    assert isinstance(app, Flask)


def test_app_config_testing(app):
    """TESTING flag is set on the test app."""
    assert app.config['TESTING'] is True


def test_app_secret_key_set(app):
    """SECRET_KEY is not empty."""
    assert app.config['SECRET_KEY']


def test_app_uses_memory_db(app):
    """Database URL is the in-memory SQLite URI we set."""
    assert 'memory' in app.config['SQLALCHEMY_DATABASE_URI']


# ── 2. Database tables created on startup ─────────────────────────────────────

def test_tables_created(app):
    """All expected tables exist in the database."""
    from app.models import db
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
    expected = {
        'locations', 'spots', 'yard_tracks', 'customers',
        'cars', 'work_orders', 'spot_assignments', 'yard_cars',
        'cleaning_entries', 'schedule_entries', 'monthly_targets',
        'comments', 'activity_log', 'users', 'gantt_marks',
    }
    missing = expected - set(tables)
    assert not missing, f'Missing tables: {missing}'


def test_seed_locations_present(db_session):
    """Seed data created the three shop locations."""
    from app.models import Location
    names = {loc.name for loc in Location.query.all()}
    assert {'Thornfield', 'Harwick', 'Delverton'} == names


def test_spots_seeded(db_session):
    """Spots were created for each location."""
    from app.models import Spot
    assert Spot.query.count() > 0


def test_spot_location_relationship(db_session):
    """Each spot belongs to a location."""
    from app.models import Spot, Location
    loc = Location.query.filter_by(name='Thornfield').first()
    assert loc is not None
    spots = Spot.query.filter_by(location_id=loc.id).all()
    assert len(spots) > 0
    for spot in spots:
        assert spot.location_id == loc.id


def test_yard_tracks_seeded(db_session):
    """Yard tracks were created."""
    from app.models import YardTrack
    assert YardTrack.query.count() > 0


def test_users_seeded(db_session):
    """Users were created."""
    from app.models import User
    assert User.query.count() > 0


# ── 3. Routes return expected status codes ────────────────────────────────────

def test_login_page_get(client):
    """Login page returns 200."""
    resp = client.get('/')
    assert resp.status_code == 200


def test_dashboard_redirects_without_login(client):
    """Dashboard redirects to login when no session."""
    resp = client.get('/dashboard')
    assert resp.status_code in (302, 303)


def test_login_and_dashboard(client, app):
    """After logging in, dashboard returns 200."""
    with app.app_context():
        from app.models import User
        user = User.query.first()
        assert user is not None

    with client.session_transaction() as sess:
        sess['user_id'] = user.id

    resp = client.get('/dashboard')
    assert resp.status_code == 200


# ── 4. Car creation end-to-end ────────────────────────────────────────────────

def test_car_creation_end_to_end(client, app):
    """POST /car/new creates a car and work order, then redirects to car profile."""
    with app.app_context():
        from app.models import User, Location, Car, WorkOrder

        user = User.query.first()
        loc  = Location.query.filter_by(name='Thornfield').first()

        with client.session_transaction() as sess:
            sess['user_id'] = user.id

        before_car_count = Car.query.count()
        before_wo_count  = WorkOrder.query.count()

        resp = client.post('/car/new', data={
            'car_mark':          'TSTX',
            'car_number':        '999001',
            'customer_name':     'TestCo',
            'commodity':         'Water',
            'location_id':       str(loc.id),
            'reason_shopped':    'Test reason',
            'purpose':           'BAD ORDER',
            'priority':          '3',
            'estimated_revenue': '5000',
            'estimated_hours':   '20',
            'date_arrived':      '2026-01-15',
        }, follow_redirects=False)

        # Should redirect to car profile
        assert resp.status_code in (302, 303)

        # Car and WO were created
        assert Car.query.count() == before_car_count + 1
        assert WorkOrder.query.count() == before_wo_count + 1

        created_car = Car.query.filter_by(car_mark='TSTX', car_number='999001').first()
        assert created_car is not None
        assert created_car.location_id == loc.id


def test_car_creation_validation_rejects_empty_mark(client, app):
    """POST /car/new with blank car mark flashes an error and redirects."""
    with app.app_context():
        from app.models import User

        user = User.query.first()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id

        resp = client.post('/car/new', data={
            'car_mark':   '',
            'car_number': '123456',
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert b'Car mark is required' in resp.data


def test_car_creation_validation_rejects_non_numeric_number(client, app):
    """POST /car/new with non-numeric car number flashes an error."""
    with app.app_context():
        from app.models import User

        user = User.query.first()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id

        resp = client.post('/car/new', data={
            'car_mark':   'TSTX',
            'car_number': 'ABC',
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert b'Car number must contain only digits' in resp.data


# ── 5. Location / spot relationship integrity ─────────────────────────────────

def test_thornfield_has_cleaning_spots(db_session):
    """Thornfield has at least one CL-N cleaning rack spot."""
    from app.models import Spot, Location
    loc = Location.query.filter_by(name='Thornfield').first()
    cl_spots = [s for s in Spot.query.filter_by(location_id=loc.id).all()
                if s.name.startswith('CL-')]
    assert len(cl_spots) > 0


def test_harwick_has_bay_e_spots(db_session):
    """Harwick has at least one Bay-E spot."""
    from app.models import Spot, Location
    loc = Location.query.filter_by(name='Harwick').first()
    bay_spots = [s for s in Spot.query.filter_by(location_id=loc.id).all()
                 if s.name.startswith('Bay-E-')]
    assert len(bay_spots) > 0


def test_delverton_has_bay_c_spots(db_session):
    """Delverton has at least one Bay-C spot."""
    from app.models import Spot, Location
    loc = Location.query.filter_by(name='Delverton').first()
    bay_spots = [s for s in Spot.query.filter_by(location_id=loc.id).all()
                 if s.name.startswith('Bay-C-')]
    assert len(bay_spots) > 0


def test_all_spots_belong_to_valid_location(db_session):
    """Every spot's location_id maps to an existing location."""
    from app.models import Spot, Location
    loc_ids = {loc.id for loc in Location.query.all()}
    for spot in Spot.query.all():
        assert spot.location_id in loc_ids, \
            f'Spot {spot.name} has invalid location_id {spot.location_id}'
