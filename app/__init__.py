import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .models import db, Location, Spot, YardTrack, Customer, User, Car, WorkOrder, MonthlyTarget, GanttMark
from datetime import date
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

    # ── Sample Cars + Work Orders ─────────────────────────────────
    if not Car.query.first():
        kelvix  = Customer.query.filter_by(name='Kelvix').first()
        proxar  = Customer.query.filter_by(name='Proxar').first()
        duratek = Customer.query.filter_by(name='Duratek').first()
        voltan  = Customer.query.filter_by(name='Voltan').first()
        crestex = Customer.query.filter_by(name='Crestex').first()
        ferrix  = Customer.query.filter_by(name='Ferrix').first()

        def add_car(loc, cust, mark, number, commodity, wo_fields):
            """Create a Car and its first WorkOrder together."""
            car = Car(
                location_id=loc.id,
                customer_id=cust.id,
                car_mark=mark,
                car_number=number,
                commodity=commodity,
                created_by='System',
            )
            db.session.add(car)
            db.session.flush()  # assigns car.id without full commit
            wo = WorkOrder(car_id=car.id, location_id=loc.id, visit_number=1, **wo_fields)
            db.session.add(wo)

        # ── Thornfield ────────────────────────────────────────────
        add_car(lachine, kelvix, 'KVLX', '183924', 'Gasoline', dict(
            reason_shopped='B/O: leaking belly',
            purpose='BAD ORDER', priority=2,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=7800.0, estimated_hours=36.0,
            status='Completed', is_closed=True,
            date_arrived=date(2026, 2, 5),
            shopping_pkg_received=date(2025, 9, 11),
            inbound_inspection=date(2026, 2, 12),
            estimate_sent=date(2026, 2, 14),
            estimate_approved=date(2026, 2, 19),
            work_order_created=date(2026, 2, 22),
            cleaning_completed=date(2026, 2, 28),
            repair_start_date=date(2026, 3, 2),
            repair_completed_date=date(2026, 3, 5),
            projected_outbound=date(2026, 3, 6),
            outbound_inspection=date(2026, 3, 6),
            dispo_requested=date(2026, 3, 10),
            dispo_received=date(2026, 3, 11),
            final_estimate_sent=date(2026, 3, 3),
            final_estimate_approved=date(2026, 3, 4),
            created_by='CSR 1',
        ))

        add_car(lachine, proxar, 'PRAX', '364817', 'Asphalt', dict(
            reason_shopped='FULL QUALIFICATION',
            purpose='Full Qualification', priority=2,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=11500.0, estimated_hours=55.0,
            status='Dispo Received',
            date_arrived=date(2025, 12, 26),
            shopping_pkg_received=date(2026, 1, 15),
            inbound_inspection=date(2026, 1, 16),
            estimate_sent=date(2026, 1, 22),
            estimate_approved=date(2026, 1, 23),
            work_order_created=date(2026, 1, 23),
            cleaning_completed=date(2026, 2, 6),
            repair_start_date=date(2026, 2, 9),
            repair_completed_date=date(2026, 2, 13),
            projected_outbound=date(2026, 2, 20),
            outbound_inspection=date(2026, 2, 25),
            dispo_requested=date(2026, 2, 26),
            dispo_received=date(2026, 3, 2),
            final_estimate_sent=date(2026, 3, 5),
            final_estimate_approved=date(2026, 3, 9),
            created_by='CSR 1',
        ))

        add_car(lachine, duratek, 'DRTX', '529103', 'Crude', dict(
            reason_shopped='Bad order valves',
            purpose='BAD ORDER', priority=2,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=6300.0, estimated_hours=28.0,
            status='Waiting Approval',
            date_arrived=date(2026, 3, 1),
            shopping_pkg_received=date(2026, 3, 1),
            inbound_inspection=date(2026, 3, 3),
            estimate_sent=date(2026, 3, 5),
            projected_outbound=date(2026, 3, 27),
            created_by='CSR 1',
        ))

        add_car(lachine, kelvix, 'KVLX', '847261', 'Gasoline', dict(
            reason_shopped='FULL QUALIFICATION',
            purpose='Full Qualification', priority=3,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=13500.0, estimated_hours=62.0,
            status='In Repair',
            date_arrived=date(2026, 2, 20),
            shopping_pkg_received=date(2026, 2, 18),
            inbound_inspection=date(2026, 2, 22),
            estimate_sent=date(2026, 2, 24),
            estimate_approved=date(2026, 2, 25),
            work_order_created=date(2026, 2, 26),
            cleaning_completed=date(2026, 3, 1),
            repair_start_date=date(2026, 3, 5),
            projected_outbound=date(2026, 3, 27),
            created_by='CSR 1',
        ))

        # ── Harwick ───────────────────────────────────────────────
        add_car(sarnia, voltan, 'VLTX', '092847', 'Bitumen', dict(
            reason_shopped='Full Qualification',
            purpose='Full Qualification', priority=2,
            estimated_revenue=10500.0, estimated_hours=52.0,
            status='Completed', is_closed=True,
            date_arrived=date(2026, 2, 1),
            shopping_pkg_received=date(2026, 2, 1),
            inbound_inspection=date(2026, 2, 3),
            estimate_sent=date(2026, 2, 5),
            estimate_approved=date(2026, 2, 6),
            work_order_created=date(2026, 2, 7),
            cleaning_completed=date(2026, 2, 10),
            repair_start_date=date(2026, 2, 12),
            repair_completed_date=date(2026, 2, 28),
            projected_outbound=date(2026, 3, 2),
            outbound_inspection=date(2026, 3, 2),
            dispo_requested=date(2026, 3, 3),
            dispo_received=date(2026, 3, 4),
            final_estimate_sent=date(2026, 3, 5),
            final_estimate_approved=date(2026, 3, 6),
            created_by='CSR 2',
        ))

        add_car(sarnia, crestex, 'CREX', '318274', 'Chemicals', dict(
            reason_shopped='BAD ORDER',
            purpose='BAD ORDER', priority=2,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=5200.0, estimated_hours=22.0,
            status='In Repair',
            date_arrived=date(2026, 3, 5),
            shopping_pkg_received=date(2026, 3, 5),
            inbound_inspection=date(2026, 3, 7),
            estimate_sent=date(2026, 3, 9),
            repair_start_date=date(2026, 3, 12),
            projected_outbound=date(2026, 4, 2),
            created_by='CSR 2',
        ))

        # ── Delverton ─────────────────────────────────────────────
        add_car(raymond, ferrix, 'FRIX', '748291', 'Ethanol', dict(
            reason_shopped='Cleaning + Inspection',
            purpose='Cleaning Only', priority=3,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=1900.0, estimated_hours=7.0,
            status='Completed', is_closed=True,
            date_arrived=date(2026, 3, 1),
            shopping_pkg_received=date(2026, 3, 1),
            inbound_inspection=date(2026, 3, 2),
            work_order_created=date(2026, 3, 2),
            cleaning_completed=date(2026, 3, 3),
            repair_completed_date=date(2026, 3, 3),
            projected_outbound=date(2026, 3, 3),
            outbound_inspection=date(2026, 3, 3),
            created_by='CSR 3',
        ))

        add_car(raymond, duratek, 'MRAX', '603947', 'Naphtha', dict(
            reason_shopped='Full Qual + Cleaning',
            purpose='Full Qualification', priority=2,
            car_type='Tank Car', cleaning_required=True, parts_status='Available',
            estimated_revenue=12400.0, estimated_hours=54.0,
            status='Waiting Cleaning',
            date_arrived=date(2026, 3, 8),
            shopping_pkg_received=date(2026, 3, 8),
            inbound_inspection=date(2026, 3, 9),
            estimate_sent=date(2026, 3, 10),
            estimate_approved=date(2026, 3, 11),
            work_order_created=date(2026, 3, 11),
            projected_outbound=date(2026, 3, 27),
            created_by='CSR 3',
        ))

        db.session.commit()