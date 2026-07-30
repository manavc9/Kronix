import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .models import db, Location, Spot, YardTrack, Customer, User, Car
from dotenv import load_dotenv

load_dotenv()

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    flask_env = os.environ.get('FLASK_ENV', 'production')
    is_dev    = flask_env == 'development'

    # ── Configuration ─────────────────────────────────────────────
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///railops.db',
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        'kronix-dev-key-2026' if is_dev else None,
    )
    if not app.config['SECRET_KEY']:
        raise RuntimeError('SECRET_KEY environment variable must be set in production.')

    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.debug = is_dev

    # ── Initialize extensions ─────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_data()

    # ── Register routes ───────────────────────────────────────────
    from .routes import main
    app.register_blueprint(main)

    return app


def _seed_data():
    """
    Populate the database with initial data on first run.
    Safe to call every startup — checks before inserting.
    """

    # ── Locations ─────────────────────────────────────────────────
    if not Location.query.first():
        db.session.add_all([
            Location(name='Thornfield'),
            Location(name='Harwick'),
            Location(name='Delverton'),
        ])
        db.session.commit()

    lachine = Location.query.filter_by(name='Thornfield').first()
    sarnia  = Location.query.filter_by(name='Harwick').first()
    raymond = Location.query.filter_by(name='Delverton').first()

    # ── Shop Spots ────────────────────────────────────────────────
    if not Spot.query.first():
        db.session.add_all([
            # Thornfield — cleaning rack + main repair
            Spot(location_id=lachine.id, name='CL-1'),
            Spot(location_id=lachine.id, name='CL-2'),
            Spot(location_id=lachine.id, name='CL-3'),
            Spot(location_id=lachine.id, name='Bay-A-1'),
            Spot(location_id=lachine.id, name='Bay-A-2'),
            Spot(location_id=lachine.id, name='Bay-B-1'),
            Spot(location_id=lachine.id, name='Bay-B-2'),
            Spot(location_id=lachine.id, name='SP-1'),
            # Harwick — cleaning rack + indoor/outdoor repair
            Spot(location_id=sarnia.id,  name='CL-1'),
            Spot(location_id=sarnia.id,  name='CL-2'),
            Spot(location_id=sarnia.id,  name='Bay-E-1'),
            Spot(location_id=sarnia.id,  name='Bay-E-2'),
            Spot(location_id=sarnia.id,  name='Bay-F-1'),
            Spot(location_id=sarnia.id,  name='Bay-F-2'),
            # Delverton — cleaning rack + main repair
            Spot(location_id=raymond.id, name='CL-1'),
            Spot(location_id=raymond.id, name='CL-2'),
            Spot(location_id=raymond.id, name='Bay-C-1'),
            Spot(location_id=raymond.id, name='Bay-D-1'),
        ])
        db.session.commit()

    # ── Yard Tracks ───────────────────────────────────────────────
    if not YardTrack.query.first():
        db.session.add_all([
            YardTrack(location_id=lachine.id, name='Yard Lead North'),
            YardTrack(location_id=lachine.id, name='Yard Lead South'),
            YardTrack(location_id=lachine.id, name='Holding Track 1'),
            YardTrack(location_id=lachine.id, name='Holding Track 2'),
            YardTrack(location_id=sarnia.id,  name='North Siding'),
            YardTrack(location_id=sarnia.id,  name='South Siding'),
            YardTrack(location_id=sarnia.id,  name='Staging Track'),
            YardTrack(location_id=raymond.id, name='Inbound Lead'),
            YardTrack(location_id=raymond.id, name='Outbound Lead'),
        ])
        db.session.commit()

    # ── Customers ─────────────────────────────────────────────────
    if not Customer.query.first():
        db.session.add_all([
            Customer(name='Kelvix'),
            Customer(name='Proxar'),
            Customer(name='Duratek'),
            Customer(name='Voltan'),
            Customer(name='Crestex'),
            Customer(name='Ferrix'),
            Customer(name='Elpax'),
        ])
        db.session.commit()

    # ── Users ─────────────────────────────────────────────────────
    if not User.query.first():
        db.session.add_all([
            User(name='Scheduler 1',   role='Scheduler',        location_id=None),
            User(name='CSR 1',         role='Customer Service', location_id=lachine.id),
            User(name='CSR 2',         role='Customer Service', location_id=sarnia.id),
            User(name='CSR 3',         role='Customer Service', location_id=raymond.id),
            User(name='Shop Manager 1', role='Shop Manager',    location_id=lachine.id),
            User(name='Shop Manager 2', role='Shop Manager',    location_id=sarnia.id),
            User(name='Shop Manager 3', role='Shop Manager',    location_id=raymond.id),
            User(name='Admin 1',        role='Admin',           location_id=None),
        ])
        db.session.commit()

    # ── Full demo dataset ─────────────────────────────────────────
    if not Car.query.first():
        from .demo_seed import run as _run_demo
        _run_demo()