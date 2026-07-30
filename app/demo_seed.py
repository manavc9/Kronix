"""
app/demo_seed.py
----------------
Full demo dataset generator (~270 cars).
Called automatically by _seed_data() on first startup when the
cars table is empty.  Safe to call directly for local resets too.

Must be called inside an active Flask app context.
"""

import random
from datetime import date, timedelta, datetime

from .models import (
    db, Location, Customer, Car, WorkOrder,
    Comment, ActivityLog, ScheduleEntry,
    YardCar, YardTrack, CleaningEntry, MonthlyTarget,
)

# ── Reference pools ───────────────────────────────────────────────────────────

REQUIRED_CUSTOMERS = [
    'Kelvix', 'Proxar', 'Duratek', 'Voltan', 'Crestex', 'Ferrix',
    'Elpax', 'Meridian Rail', 'Norline', 'Ridgeway Freight', 'Transcorp', 'Altavex',
]

CAR_MARKS = [
    'KVLX', 'PRAX', 'DRTX', 'VLTX', 'CREX', 'FRIX', 'MRAX',
    'ELQX', 'ZOLX', 'BRNX', 'NRLX', 'TCPX', 'ALVX', 'RWFX',
]

COMMODITIES = [
    'Gasoline', 'Asphalt', 'Crude', 'Naphtha', 'Chemicals',
    'Ethanol', 'Bitumen', 'Diesel', 'Lube Oil', 'Corn Syrup',
]

PURPOSES  = ['Bad Order', 'Full Qualification', 'Partial Qualification',
             'Railroad Damage', 'Lining Inspection', 'Reline', 'Cleaning']
PURPOSE_W = [35, 30, 15, 8, 5, 4, 3]

CAR_TYPES = (['Tank Car'] * 14 + ['Pressure Car'] * 3 +
             ['Hopper'] * 2 + ['Gondola'] * 1)

PARTS_STATUSES = ['Available', 'Partially Available', 'Ordered', 'Waiting ETA', 'Unknown']
PARTS_W        = [50, 15, 20, 10, 5]

REASONS = {
    'Bad Order': [
        'B/O: Leaking bottom outlet valve',
        'B/O: Leaking dome cover gasket',
        'B/O: Pressure test failure',
        'B/O: Broken sill — yard impact',
        'B/O: Leaking eduction pipe',
        'B/O: Failed pressure relief valve',
        'B/O: Cracked center sill weld',
    ],
    'Full Qualification': [
        'FULL QUALIFICATION — 10yr DOT requirement',
        'FULL QUALIFICATION — 5yr internal inspection',
        'FULL QUAL + RELINE — scheduled',
        'FULL QUAL — AAR compliance',
    ],
    'Partial Qualification': [
        'Partial qual — valve assembly overhaul',
        'Partial qual — brake system rebuild',
        'Partial qual — interior lining inspection only',
    ],
    'Railroad Damage': [
        'Railroad damage — derailment, body damage',
        'Railroad damage — coupler struck in yard',
        'Railroad damage — stub sill bent',
        'Railroad damage — body bolster cracked',
    ],
    'Lining Inspection': [
        'Lining inspection — scheduled maintenance',
        'Lining inspection — customer request',
        'Interior lining check — leakage concern',
    ],
    'Reline': [
        'Full reline — lining failed pressure test',
        'Partial reline + valve repack',
        'Reline + interior sandblast',
    ],
    'Cleaning': [
        'Cleaning only — product changeover',
        'Deep clean + inspection — prior to qualification',
        'Product residue removal',
        'Steam clean — asphalt residue',
    ],
}

COMMENT_POOL = [
    'Waiting on BOV cap gasket from supplier',
    'Customer approved additional repairs',
    'Parts arrived, repair starting tomorrow',
    'Outbound inspection passed first attempt',
    'Customer requested expedited turnaround',
    'Waiting for D3 form from customer',
    'Running board replacement added to SOW',
    'Car held pending customer approval on estimate',
    'Parts ETA confirmed — delivery expected soon',
    'Rework required — weld failed inspection',
    'Estimate revised after interior inspection findings',
    'Additional valve damage found during teardown',
    'Customer confirmed return location: home shop',
    'Lining thinner than spec — full reline added to scope',
    'Priority elevated by customer request',
]

AUTHORS = [
    ('CSR 1',                    'Customer Service'),
    ('CSR 2',                    'Customer Service'),
    ('CSR 3',                    'Customer Service'),
    ('Shop Manager Thornfield',  'Shop Manager'),
    ('Shop Manager Harwick',     'Shop Manager'),
    ('Shop Manager Delverton',   'Shop Manager'),
    ('Scheduler 1',              'Scheduler'),
]

# ── Stage distributions ───────────────────────────────────────────────────────

THORNFIELD_STAGES = [   # total = 87
    ('To Arrive',          11),
    ('Arrived',            10),
    ('Waiting Estimate',    4),
    ('Waiting Approval',    5),
    ('Waiting Work Order',  4),
    ('Work Order Created', 11),
    ('Waiting Cleaning',    5),
    ('In Cleaning',         4),
    ('In Repair',           9),
    ('Waiting Material',    4),
    ('Waiting Repair',      3),
    ('Repair Complete',     3),
    ('Waiting Dispo',       3),
    ('Dispo Received',      2),
    ('Ready to Bill',       1),
    ('Completed',           8),
    ('Billed',              1),
]

DELVERTON_STAGES = [   # total = 74
    ('To Arrive',           9),
    ('Arrived',             8),
    ('Waiting Estimate',    4),
    ('Waiting Approval',    4),
    ('Waiting Work Order',  3),
    ('Work Order Created',  9),
    ('Waiting Cleaning',    5),
    ('In Cleaning',         3),
    ('In Repair',           8),
    ('Waiting Material',    4),
    ('Waiting Repair',      2),
    ('Repair Complete',     3),
    ('Waiting Dispo',       3),
    ('Dispo Received',      2),
    ('Ready to Bill',       1),
    ('Completed',           4),
    ('Billed',              2),
]

HARWICK_STAGES = [    # total = 61
    ('To Arrive',           8),
    ('Arrived',             7),
    ('Waiting Estimate',    4),
    ('Waiting Approval',    4),
    ('Waiting Work Order',  3),
    ('Work Order Created',  9),
    ('Waiting Cleaning',    4),
    ('In Cleaning',         2),
    ('In Repair',           7),
    ('Waiting Material',    4),
    ('Waiting Repair',      2),
    ('Repair Complete',     2),
    ('Waiting Dispo',       2),
    ('Dispo Received',      1),
    ('Ready to Bill',       0),
    ('Completed',           2),
    ('Billed',              0),
]

# ── Revenue / hours / repair-duration tables ──────────────────────────────────

REV_RANGES = {
    'Bad Order':             (3000,  12000),
    'Full Qualification':    (8000,  25000),
    'Partial Qualification': (4000,  15000),
    'Railroad Damage':       (5000,  20000),
    'Lining Inspection':     (2000,   6000),
    'Reline':               (15000,  45000),
    'Cleaning':              (1500,   4000),
}
HRS_RANGES = {
    'Bad Order':             (8,   40),
    'Full Qualification':    (40, 120),
    'Partial Qualification': (20,  60),
    'Railroad Damage':       (20,  80),
    'Lining Inspection':     (8,   24),
    'Reline':                (60, 180),
    'Cleaning':              (4,   16),
}
REPAIR_DAYS = {
    'Cleaning':              (3,   5),
    'Bad Order':             (7,  14),
    'Lining Inspection':     (5,  10),
    'Partial Qualification': (14, 28),
    'Railroad Damage':       (14, 35),
    'Full Qualification':    (14, 30),
    'Reline':                (10, 20),
}

STAGE_LOOKBACK = {
    'Arrived':           (1,  14),
    'Waiting Estimate':  (10, 40),
    'Waiting Approval':  (15, 50),
    'Waiting Work Order':(20, 55),
    'Work Order Created':(25, 65),
    'Waiting Cleaning':  (30, 70),
    'In Cleaning':       (35, 75),
    'Waiting Repair':    (38, 80),
    'In Repair':         (40, 90),
    'Waiting Material':  (40, 90),
    'Repair Complete':   (55, 110),
    'Waiting Dispo':     (60, 120),
    'Dispo Received':    (65, 130),
    'Ready to Bill':     (68, 135),
    'Billed':            (75, 150),
    'Completed':         (80, 210),
}

LOC_TARGETS = {
    'Thornfield': (33, 520000.0),
    'Delverton':  (28, 350000.0),
    'Harwick':    (24, 265000.0),
}

_FIELD_ROLES = [
    ('date_arrived',            'Scheduler'),
    ('shopping_pkg_received',   'Customer Service'),
    ('inbound_inspection',      'Customer Service'),
    ('estimate_sent',           'Customer Service'),
    ('estimate_approved',       'Customer Service'),
    ('work_order_created',      'Customer Service'),
    ('cleaning_scheduled',      'Scheduler'),
    ('cleaning_completed',      'Scheduler'),
    ('repair_start_date',       'Shop Manager'),
    ('repair_completed_date',   'Shop Manager'),
    ('outbound_inspection',     'Customer Service'),
    ('dispo_requested',         'Customer Service'),
    ('dispo_received',          'Customer Service'),
    ('billed_out',              'Customer Service'),
    ('final_estimate_sent',     'Customer Service'),
    ('final_estimate_approved', 'Customer Service'),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _unique_number(mark: str, used: set) -> str:
    while True:
        n = str(random.randint(100000, 999999))
        if (mark, n) not in used:
            used.add((mark, n))
            return n


def _rand_rev(purpose):
    lo, hi = REV_RANGES.get(purpose, (3000, 10000))
    return round(random.uniform(lo, hi), 2)


def _rand_hrs(purpose):
    lo, hi = HRS_RANGES.get(purpose, (16, 48))
    return round(random.uniform(lo, hi), 1)


def _expand(stage_weights):
    result = []
    for stage, count in stage_weights:
        result.extend([stage] * count)
    random.shuffle(result)
    return result


def _build_fields(stage: str, purpose: str, cleaning_req: bool,
                  today: date, history: bool = False) -> dict:
    CLEANING_STAGES = {'Waiting Cleaning', 'In Cleaning'}
    if stage in CLEANING_STAGES:
        cleaning_req = True

    if stage == 'To Arrive':
        return {'status': 'To Arrive', 'is_closed': False}

    if stage == 'Arrived':
        return {
            'date_arrived': today - timedelta(days=random.randint(1, 14)),
            'status': 'Arrived',
            'is_closed': False,
        }

    lo, hi = STAGE_LOOKBACK.get(stage, (30, 90))
    if history:
        lo, hi = 120, 210

    cur = today - timedelta(days=random.randint(lo, hi))
    f: dict = {}

    def step(lo_d: int, hi_d: int) -> date:
        nonlocal cur
        nxt = cur + timedelta(days=random.randint(lo_d, hi_d))
        cur = min(nxt, today)
        return cur

    f['date_arrived']          = cur
    f['shopping_pkg_received'] = step(2, 5)
    f['inbound_inspection']    = step(3, 7)

    if stage == 'Waiting Estimate':
        return {**f, 'status': 'Waiting Estimate', 'is_closed': False}

    f['estimate_sent'] = step(1, 3)

    if stage == 'Waiting Approval':
        return {**f, 'status': 'Waiting Approval', 'is_closed': False}

    f['estimate_approved'] = step(3, 14)

    if stage == 'Waiting Work Order':
        return {**f, 'status': 'Waiting Work Order', 'is_closed': False}

    f['work_order_created'] = step(1, 2)

    if stage == 'Work Order Created':
        return {**f, 'status': 'Work Order Created', 'is_closed': False}

    if cleaning_req:
        f['cleaning_scheduled'] = step(2, 5)

        if stage == 'Waiting Cleaning':
            return {**f, 'status': 'Waiting Cleaning', 'is_closed': False}

        if stage == 'In Cleaning':
            return {**f, 'status': 'In Cleaning', 'is_closed': False}

        f['cleaning_completed'] = step(3, 7)

    if stage == 'Waiting Repair':
        return {**f, 'status': 'Waiting Repair', 'is_closed': False}

    f['repair_start_date'] = step(1, 3)
    r_lo, r_hi = REPAIR_DAYS.get(purpose, (7, 21))
    f['projected_outbound'] = f['repair_start_date'] + timedelta(
        days=random.randint(r_lo, r_hi + 5))

    if stage == 'In Repair':
        return {**f, 'status': 'In Repair', 'is_closed': False}

    if stage == 'Waiting Material':
        return {**f, 'status': 'Waiting Material', 'is_closed': False}

    f['repair_completed_date'] = step(r_lo, r_hi)
    f['actual_hours'] = round(_rand_hrs(purpose) * random.uniform(0.8, 1.2), 1)

    if stage == 'Repair Complete':
        return {**f, 'status': 'Repair Complete', 'is_closed': False}

    f['outbound_inspection'] = step(1, 2)
    f['dispo_requested']     = f['outbound_inspection']

    if stage == 'Waiting Dispo':
        return {**f, 'status': 'Waiting Dispo', 'is_closed': False}

    f['dispo_received'] = step(2, 7)

    if stage == 'Dispo Received':
        return {**f, 'status': 'Dispo Received', 'is_closed': False}

    if stage == 'Ready to Bill':
        return {**f, 'status': 'Ready to Bill', 'is_closed': False}

    f['billed_out']          = step(1, 3)
    f['final_estimate_sent'] = f['billed_out']

    if stage == 'Billed':
        return {**f, 'status': 'Billed', 'is_closed': False}

    f['final_estimate_approved'] = step(3, 10)

    if history and f.get('dispo_received'):
        target = today - timedelta(days=random.randint(30, 90))
        if target > f['dispo_received']:
            f['billed_out']              = target
            f['final_estimate_sent']     = target
            f['final_estimate_approved'] = min(
                target + timedelta(days=random.randint(3, 10)), today)

    return {**f, 'status': 'Completed', 'is_closed': True}


def _make_activity(wo_id: int, fields: dict) -> list:
    logs = []
    for field, role in _FIELD_ROLES:
        val = fields.get(field)
        if not val:
            continue
        candidates = [a for a in AUTHORS if a[1] == role] or AUTHORS
        author = random.choice(candidates)
        ts = datetime.combine(val, datetime.min.time()) + timedelta(
            hours=random.randint(8, 17), minutes=random.randint(0, 59))
        logs.append(ActivityLog(
            work_order_id=wo_id,
            user=author[0], role=author[1],
            action=f'Stamped {field}',
            field_name=field,
            old_value=None,
            new_value=str(val),
            created_at=ts,
        ))
    return logs


def _create_car_and_wo(loc, customer, purpose, stage, cleaning_req,
                       creator, today, used_combos, history=False):
    mark   = random.choice(CAR_MARKS)
    number = _unique_number(mark, used_combos)

    car = Car(
        location_id=loc.id, customer_id=customer.id,
        car_mark=mark, car_number=number,
        commodity=random.choice(COMMODITIES),
        created_by=creator,
    )
    db.session.add(car)
    db.session.flush()

    fields    = _build_fields(stage, purpose, cleaning_req, today, history)
    status    = fields.pop('status')
    is_closed = fields.pop('is_closed')
    actual_h  = fields.pop('actual_hours', 0.0)

    est_rev = _rand_rev(purpose)
    est_hrs = _rand_hrs(purpose)

    wo = WorkOrder(
        car_id=car.id, location_id=loc.id,
        visit_number=1,
        reason_shopped=random.choice(REASONS[purpose]),
        purpose=purpose,
        priority=random.choices([1, 2, 3], weights=[10, 40, 50], k=1)[0],
        car_type=random.choice(CAR_TYPES),
        cleaning_required=cleaning_req,
        parts_status=random.choices(PARTS_STATUSES, weights=PARTS_W, k=1)[0],
        estimated_revenue=est_rev,
        estimated_hours=est_hrs,
        actual_hours=actual_h,
        created_by=creator, updated_by=creator,
        **fields,
    )
    wo.status    = status
    wo.is_closed = is_closed
    db.session.add(wo)
    db.session.flush()

    return car, wo, fields, status, is_closed, est_rev, est_hrs


def _seed_location(loc, customers, stages, creator,
                   tracks, clean_used, today, used_combos):
    cars_n = sched_n = yard_n = clean_n = 0

    for stage in stages:
        customer     = random.choice(customers)
        purpose      = random.choices(PURPOSES, weights=PURPOSE_W, k=1)[0]
        cleaning_req = (
            purpose in ('Bad Order', 'Full Qualification',
                        'Partial Qualification', 'Reline')
            or random.random() < 0.45
        )

        car, wo, fields, status, is_closed, est_rev, est_hrs = _create_car_and_wo(
            loc, customer, purpose, stage, cleaning_req,
            creator, today, used_combos)
        cars_n += 1

        db.session.add_all(_make_activity(wo.id, fields))

        if random.random() < 0.30:
            for _ in range(random.randint(1, 3)):
                author = random.choice(AUTHORS)
                ts = datetime.utcnow() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23))
                db.session.add(Comment(
                    work_order_id=wo.id,
                    author=author[0], role=author[1],
                    body=random.choice(COMMENT_POOL),
                    created_at=ts,
                ))

        if not is_closed and tracks:
            track = random.choice(tracks)
            ys_map = {
                'To Arrive':       'To Arrive',
                'Arrived':         'Just Inbounded',
                'In Repair':       'In Yard Repair',
                'Waiting Material':'In Yard Repair',
                'Dispo Received':  'In Yard',
                'Ready to Bill':   'In Yard',
                'Billed':          'In Yard',
            }
            db.session.add(YardCar(
                work_order_id=wo.id, track_id=track.id,
                yard_status=ys_map.get(status, 'In Yard'),
                is_active=True, updated_by=creator,
            ))
            yard_n += 1

        if (not is_closed
                and fields.get('work_order_created')
                and random.random() < 0.60):
            proj = fields.get('projected_outbound')
            t_week = min(4, max(1, (proj.day - 1) // 7 + 1)) if proj else None
            db.session.add(ScheduleEntry(
                work_order_id=wo.id, location_id=loc.id,
                month=today.month, year=today.year,
                target_week=t_week, target_date=proj,
                schedule_status='Scheduled',
                rev_per_hour=round(est_rev / est_hrs, 2) if est_hrs else 0.0,
                priority_score=round(random.uniform(0.5, 5.0), 2),
                scheduled_by=creator,
            ))
            sched_n += 1

        if (cleaning_req
                and fields.get('cleaning_scheduled')
                and purpose in ('Bad Order', 'Full Qualification',
                                'Partial Qualification', 'Reline')):
            max_pos = 14 if loc.name == 'Delverton' else (5 if loc.name == 'Harwick' else 7)
            used    = clean_used.setdefault(loc.id, set())
            free    = [p for p in range(1, max_pos + 1) if p not in used]
            pos     = None
            if free:
                pos = random.choice(free)
                used.add(pos)
            c_status = ('Cleaned'     if fields.get('cleaning_completed') else
                        'In Cleaning' if status == 'In Cleaning' else
                        'Scheduled')
            db.session.add(CleaningEntry(
                work_order_id=wo.id, location_id=loc.id,
                rack_position=pos,
                scheduled_date=fields['cleaning_scheduled'],
                cleaning_status=c_status,
            ))
            clean_n += 1

    db.session.commit()
    return cars_n, sched_n, yard_n, clean_n


def _seed_history(locations, customers, today, used_combos):
    pool = (locations * 14)[:40]
    random.shuffle(pool)
    added = 0
    for loc in pool:
        customer     = random.choice(customers)
        purpose      = random.choices(PURPOSES, weights=PURPOSE_W, k=1)[0]
        cleaning_req = random.random() < 0.6
        _create_car_and_wo(
            loc, customer, purpose, 'Completed',
            cleaning_req, 'Scheduler 1', today, used_combos, history=True)
        added += 1
    db.session.commit()
    return added


def _seed_monthly_targets(locations, today):
    added = 0
    for loc in locations:
        car_t, rev_t = LOC_TARGETS.get(loc.name, (30, 400000.0))
        for offset in range(3):
            m = today.month - offset
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            exists = MonthlyTarget.query.filter_by(
                location_id=loc.id, month=m, year=y).first()
            if not exists:
                db.session.add(MonthlyTarget(
                    location_id=loc.id, month=m, year=y,
                    car_target=car_t, revenue_target=rev_t,
                    created_by='Scheduler 1',
                ))
                added += 1
    db.session.commit()
    return added


# ── Public entry point ────────────────────────────────────────────────────────

def run(print_summary: bool = False) -> bool:
    """
    Seed the full demo dataset.  Must be called inside an app context.

    Returns True if seeding ran, False if skipped (DB already populated).
    Idempotent: skips if more than 50 cars already exist.
    """
    existing = Car.query.count()
    if existing > 50:
        if print_summary:
            print(f'Demo seed skipped — {existing} cars already in database.')
        return False

    # Deterministic output; reset each call
    random.seed(42)
    used_combos: set = set()
    today = date.today()

    # Pre-load existing car numbers so new ones don't collide
    for row in db.session.execute(db.text('SELECT car_mark, car_number FROM cars')):
        used_combos.add((row[0], row[1]))

    thornfield = Location.query.filter_by(name='Thornfield').first()
    delverton  = Location.query.filter_by(name='Delverton').first()
    harwick    = Location.query.filter_by(name='Harwick').first()

    if not all([thornfield, delverton, harwick]):
        raise RuntimeError(
            'Locations not found — base seed must run before demo seed.')

    # Ensure all required customers exist
    known = {c.name for c in Customer.query.all()}
    for name in REQUIRED_CUSTOMERS:
        if name not in known:
            db.session.add(Customer(name=name))
    db.session.commit()
    customers = Customer.query.all()

    def _tracks(loc):
        return YardTrack.query.filter_by(location_id=loc.id, is_active=True).all()

    clean_used: dict = {}

    lc, ls, ly, lcl = _seed_location(
        thornfield, customers, _expand(THORNFIELD_STAGES),
        'CSR 1', _tracks(thornfield), clean_used, today, used_combos)

    rc, rs, ry, rcl = _seed_location(
        delverton, customers, _expand(DELVERTON_STAGES),
        'CSR 3', _tracks(delverton), clean_used, today, used_combos)

    sc, ss, sy, scl = _seed_location(
        harwick, customers, _expand(HARWICK_STAGES),
        'CSR 2', _tracks(harwick), clean_used, today, used_combos)

    hist_n    = _seed_history([thornfield, delverton, harwick], customers, today, used_combos)
    targets_n = _seed_monthly_targets([thornfield, delverton, harwick], today)

    if print_summary:
        total      = Car.query.count()
        completed  = WorkOrder.query.filter_by(is_closed=True).count()
        print('=== Kronix Demo Data Seeded ===')
        print(f'Thornfield:          {lc} cars')
        print(f'Delverton:           {rc} cars')
        print(f'Harwick:             {sc} cars')
        print(f'History records:     {hist_n}')
        print(f'Schedule entries:    {ls + rs + ss}')
        print(f'Yard entries:        {ly + ry + sy}')
        print(f'Cleaning entries:    {lcl + rcl + scl}')
        print(f'Monthly targets:     {targets_n}')
        print(f'Completed WOs:       {completed}')
        print(f'Total cars in DB:    {total}')
        print('================================')

    return True
