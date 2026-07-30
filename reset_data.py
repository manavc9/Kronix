"""
reset_data.py
Run this to rebuild all spots, tracks, and users with generic names.
Usage: python reset_data.py
"""

from app import create_app
from app.models import db, Location, Spot, YardTrack, User

app = create_app()

with app.app_context():

    # ─────────────────────────────────────────────
    # STEP 1 — Clear existing spots, tracks, users
    # ─────────────────────────────────────────────
    print("Clearing existing spots, tracks and users...")

    db.session.execute(db.text('DELETE FROM spot_assignments'))
    db.session.execute(db.text('DELETE FROM spots'))
    db.session.execute(db.text('DELETE FROM yard_tracks'))
    db.session.execute(db.text('DELETE FROM yard_cars'))
    db.session.execute(db.text('DELETE FROM users'))
    db.session.commit()
    print("Done clearing.")

    # ─────────────────────────────────────────────
    # STEP 2 — Get locations
    # ─────────────────────────────────────────────
    thornfield = Location.query.filter_by(name='Thornfield').first()
    harwick    = Location.query.filter_by(name='Harwick').first()
    delverton  = Location.query.filter_by(name='Delverton').first()

    if not thornfield or not harwick or not delverton:
        print("ERROR: Locations not found. Run the app once first to seed locations.")
        exit(1)

    # ─────────────────────────────────────────────
    # STEP 3 — THORNFIELD SPOTS (19 total)
    # ─────────────────────────────────────────────
    print("Creating Thornfield spots...")
    thornfield_spots = [
        # Zone: Cleaning Rack (7 spots)
        Spot(location_id=thornfield.id, name='CL-1', is_active=True),
        Spot(location_id=thornfield.id, name='CL-2', is_active=True),
        Spot(location_id=thornfield.id, name='CL-3', is_active=True),
        Spot(location_id=thornfield.id, name='CL-4', is_active=True),
        Spot(location_id=thornfield.id, name='CL-5', is_active=True),
        Spot(location_id=thornfield.id, name='CL-6', is_active=True),
        Spot(location_id=thornfield.id, name='CL-7', is_active=True),
        # Zone: Main Repair — Bay A (5 spots)
        Spot(location_id=thornfield.id, name='Bay-A-1', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-A-2', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-A-3', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-A-4', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-A-5', is_active=True),
        # Zone: Main Repair — Bay B (4 spots)
        Spot(location_id=thornfield.id, name='Bay-B-1', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-B-2', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-B-3', is_active=True),
        Spot(location_id=thornfield.id, name='Bay-B-4', is_active=True),
        # Zone: Surface Prep (3 spots)
        Spot(location_id=thornfield.id, name='SP-1', is_active=True),
        Spot(location_id=thornfield.id, name='SP-2', is_active=True),
        Spot(location_id=thornfield.id, name='SP-3', is_active=True),
    ]
    db.session.add_all(thornfield_spots)

    # ─────────────────────────────────────────────
    # STEP 4 — DELVERTON SPOTS (32 total)
    # ─────────────────────────────────────────────
    print("Creating Delverton spots...")
    delverton_spots = []

    # Cleaning Rack (14 spots)
    for i in range(1, 15):
        delverton_spots.append(
            Spot(location_id=delverton.id, name=f'CL-{i}', is_active=True)
        )

    # Main Repair — Bay C (5 spots)
    for i in range(1, 6):
        delverton_spots.append(
            Spot(location_id=delverton.id, name=f'Bay-C-{i}', is_active=True)
        )

    # Main Repair — Bay D (5 spots)
    for i in range(1, 6):
        delverton_spots.append(
            Spot(location_id=delverton.id, name=f'Bay-D-{i}', is_active=True)
        )

    # Rework Lane (8 spots)
    for i in range(1, 9):
        delverton_spots.append(
            Spot(location_id=delverton.id, name=f'RW-{i}', is_active=True)
        )

    db.session.add_all(delverton_spots)

    # ─────────────────────────────────────────────
    # STEP 5 — HARWICK SPOTS (15 total)
    # ─────────────────────────────────────────────
    print("Creating Harwick spots...")
    harwick_spots = [
        # Cleaning Rack (5 spots)
        Spot(location_id=harwick.id, name='CL-1', is_active=True),
        Spot(location_id=harwick.id, name='CL-2', is_active=True),
        Spot(location_id=harwick.id, name='CL-3', is_active=True),
        Spot(location_id=harwick.id, name='CL-4', is_active=True),
        Spot(location_id=harwick.id, name='CL-5', is_active=True),
        # Indoor Repair — Bay E (7 spots)
        Spot(location_id=harwick.id, name='Bay-E-1', is_active=True),
        Spot(location_id=harwick.id, name='Bay-E-2', is_active=True),
        Spot(location_id=harwick.id, name='Bay-E-3', is_active=True),
        Spot(location_id=harwick.id, name='Bay-E-4', is_active=True),
        Spot(location_id=harwick.id, name='Bay-E-5', is_active=True),
        Spot(location_id=harwick.id, name='Bay-E-6', is_active=True),
        Spot(location_id=harwick.id, name='Bay-E-7', is_active=True),
        # Outdoor Repair — Bay F (3 spots)
        Spot(location_id=harwick.id, name='Bay-F-1', is_active=True),
        Spot(location_id=harwick.id, name='Bay-F-2', is_active=True),
        Spot(location_id=harwick.id, name='Bay-F-3', is_active=True),
    ]
    db.session.add_all(harwick_spots)

    # ─────────────────────────────────────────────
    # STEP 6 — YARD TRACKS
    # ─────────────────────────────────────────────
    print("Creating yard tracks...")
    tracks = [
        # Thornfield
        YardTrack(location_id=thornfield.id, name='Yard Lead North'),
        YardTrack(location_id=thornfield.id, name='Yard Lead South'),
        YardTrack(location_id=thornfield.id, name='Holding Track 1'),
        YardTrack(location_id=thornfield.id, name='Holding Track 2'),
        # Delverton
        YardTrack(location_id=delverton.id,  name='Inbound Lead'),
        YardTrack(location_id=delverton.id,  name='Outbound Lead'),
        # Harwick
        YardTrack(location_id=harwick.id,    name='North Siding'),
        YardTrack(location_id=harwick.id,    name='South Siding'),
        YardTrack(location_id=harwick.id,    name='Staging Track'),
    ]
    db.session.add_all(tracks)

    # ─────────────────────────────────────────────
    # STEP 7 — USERS
    # ─────────────────────────────────────────────
    print("Creating users...")
    users = [
        # Scheduler — all locations
        User(name='Scheduler 1',   role='Scheduler',        location_id=None),
        # Admin — all locations
        User(name='Admin 1',       role='Admin',            location_id=None),
        # Customer Service — all locations
        User(name='CSR 1',         role='Customer Service', location_id=None),
        User(name='CSR 2',         role='Customer Service', location_id=None),
        User(name='CSR 3',         role='Customer Service', location_id=None),
        User(name='CSR 4',         role='Customer Service', location_id=None),
        # Shop Managers
        User(name='Shop Manager 1', role='Shop Manager',    location_id=thornfield.id),
        User(name='Shop Manager 2', role='Shop Manager',    location_id=delverton.id),
        User(name='Shop Manager 3', role='Shop Manager',    location_id=harwick.id),
    ]
    db.session.add_all(users)
    db.session.commit()

    # ─────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────
    print("\n✓ All done. Summary:")
    print(f"  Thornfield spots: {Spot.query.filter_by(location_id=thornfield.id).count()}")
    print(f"  Delverton spots:  {Spot.query.filter_by(location_id=delverton.id).count()}")
    print(f"  Harwick spots:    {Spot.query.filter_by(location_id=harwick.id).count()}")
    print(f"  Yard tracks:      {YardTrack.query.count()}")
    print(f"  Users:            {User.query.count()}")
    print("\nLogin at localhost:5000 to confirm.")
