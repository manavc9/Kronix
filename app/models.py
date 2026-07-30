from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


# ─────────────────────────────────────────────
# LOCATIONS
# ─────────────────────────────────────────────
class Location(db.Model):
    __tablename__ = 'locations'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False, unique=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    spots       = db.relationship('Spot',      backref='location', lazy=True)
    yard_tracks = db.relationship('YardTrack', backref='location', lazy=True)
    cars        = db.relationship('Car',       backref='location', lazy=True)

    def __repr__(self):
        return f'<Location {self.name}>'


# ─────────────────────────────────────────────
# SHOP SPOTS
# ─────────────────────────────────────────────
class Spot(db.Model):
    __tablename__ = 'spots'
    id          = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    name        = db.Column(db.String(50), nullable=False)
    is_active   = db.Column(db.Boolean, default=True)

    assignments = db.relationship('SpotAssignment', backref='spot', lazy=True)

    @property
    def current_assignment(self):
        return SpotAssignment.query.filter_by(
            spot_id=self.id, is_active=True
        ).first()

    def __repr__(self):
        return f'<Spot {self.name}>'


# ─────────────────────────────────────────────
# YARD TRACKS
# ─────────────────────────────────────────────
class YardTrack(db.Model):
    __tablename__ = 'yard_tracks'
    id          = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    name        = db.Column(db.String(50), nullable=False)
    is_active   = db.Column(db.Boolean, default=True)

    yard_cars   = db.relationship('YardCar', backref='track', lazy=True)

    def __repr__(self):
        return f'<YardTrack {self.name}>'


# ─────────────────────────────────────────────
# CUSTOMERS
# ─────────────────────────────────────────────
class Customer(db.Model):
    __tablename__ = 'customers'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False, unique=True)
    contact_email = db.Column(db.String(150))
    contact_phone = db.Column(db.String(50))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    cars          = db.relationship('Car', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'


# ─────────────────────────────────────────────
# CAR  — permanent physical identity
# One record per railcar, exists forever.
# Never duplicated when a car returns.
# All visit history lives in WorkOrders.
# ─────────────────────────────────────────────
class Car(db.Model):
    __tablename__ = 'cars'
    id          = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    car_mark    = db.Column(db.String(20), nullable=False)
    car_number  = db.Column(db.String(20), nullable=False)
    commodity   = db.Column(db.String(100))

    is_archived = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    created_by  = db.Column(db.String(100))

    work_orders = db.relationship('WorkOrder', backref='car', lazy=True,
                                  order_by='WorkOrder.created_at.desc()')

    def __repr__(self):
        return f'<Car {self.car_mark}-{self.car_number}>'

    @property
    def full_id(self):
        return f'{self.car_mark}-{self.car_number}'

    @property
    def active_work_order(self):
        return WorkOrder.query.filter_by(
            car_id=self.id, is_closed=False
        ).order_by(WorkOrder.created_at.desc()).first()

    @property
    def visit_count(self):
        return len(self.work_orders)

    @property
    def lifetime_revenue(self):
        return sum(wo.estimated_revenue or 0 for wo in self.work_orders)


# ─────────────────────────────────────────────
# WORK ORDER  — one visit, one job
# Created every time a car comes in.
# A returning car gets a new WorkOrder,
# keeping full history of every visit.
# ─────────────────────────────────────────────
class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    id          = db.Column(db.Integer, primary_key=True)
    car_id      = db.Column(db.Integer, db.ForeignKey('cars.id'),       nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'),  nullable=False)

    visit_number    = db.Column(db.Integer, default=1)
    reason_shopped  = db.Column(db.String(255))
    scope_of_work   = db.Column(db.Text)
    purpose         = db.Column(db.String(50))
    priority        = db.Column(db.Integer, default=3)

    estimated_revenue = db.Column(db.Float, default=0.0)
    estimated_hours   = db.Column(db.Float, default=0.0)
    actual_hours      = db.Column(db.Float, default=0.0)

    status      = db.Column(db.String(50), default='Inbounded')
    is_closed   = db.Column(db.Boolean, default=False)

    # CS dates
    date_arrived            = db.Column(db.Date)
    shopping_pkg_received   = db.Column(db.Date)
    inbound_inspection      = db.Column(db.Date)
    estimate_sent           = db.Column(db.Date)
    estimate_approved       = db.Column(db.Date)
    work_order_created      = db.Column(db.Date)

    # Scheduler dates
    cleaning_scheduled      = db.Column(db.Date)
    cleaning_completed      = db.Column(db.Date)
    repair_start_date       = db.Column(db.Date)
    repair_completed_date   = db.Column(db.Date)
    projected_outbound      = db.Column(db.Date)

    # Post-repair CS dates
    outbound_inspection     = db.Column(db.Date)
    dispo_requested         = db.Column(db.Date)
    dispo_received          = db.Column(db.Date)
    billed_out              = db.Column(db.Date)
    final_estimate_sent     = db.Column(db.Date)
    final_estimate_approved = db.Column(db.Date)

    # Car type
    car_type    = db.Column(db.String(50))

    # Cleaning flag
    cleaning_required = db.Column(db.Boolean, default=False)

    # Parts tracking
    parts_status = db.Column(db.String(50), default='Unknown')
    parts_eta    = db.Column(db.Date)
    parts_notes  = db.Column(db.Text)

    # Rework
    rework_required = db.Column(db.Boolean, default=False)
    rework_date     = db.Column(db.Date)
    rework_notes    = db.Column(db.Text)
    rework_passed   = db.Column(db.Boolean, default=False)

    # Blast & Paint
    blast_paint_required     = db.Column(db.Boolean, default=False)
    bp_blast_hrs             = db.Column(db.Float, default=0.0)
    bp_interior_coating_hrs  = db.Column(db.Float, default=0.0)
    bp_lining_touchup_hrs    = db.Column(db.Float, default=0.0)
    bp_buff_lining_hrs       = db.Column(db.Float, default=0.0)
    bp_paint_booth_hrs       = db.Column(db.Float, default=0.0)
    bp_notes                 = db.Column(db.Text)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by  = db.Column(db.String(100))
    updated_by  = db.Column(db.String(100))

    comments        = db.relationship('Comment',        backref='work_order', lazy=True, cascade='all, delete-orphan')
    activity_log    = db.relationship('ActivityLog',    backref='work_order', lazy=True, cascade='all, delete-orphan')
    spot_assignments= db.relationship('SpotAssignment', backref='work_order', lazy=True)
    yard_entries    = db.relationship('YardCar',        backref='work_order', lazy=True)
    cleaning_entries= db.relationship('CleaningEntry',  backref='work_order', lazy=True)
    schedule_entries= db.relationship('ScheduleEntry',  backref='work_order', lazy=True)

    def __repr__(self):
        return f'<WorkOrder #{self.id} car={self.car_id} visit={self.visit_number}>'

    @property
    def days_on_site(self):
        if self.date_arrived:
            return (date.today() - self.date_arrived).days
        return None

    @property
    def is_overdue(self):
        if self.projected_outbound and self.status not in ('Completed', 'Cancelled'):
            return date.today() > self.projected_outbound
        return False

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (date.today() - self.projected_outbound).days
        return 0

    @property
    def rev_per_hour(self):
        if self.estimated_hours and self.estimated_hours > 0:
            return round(self.estimated_revenue / self.estimated_hours, 2)
        return 0.0

    @property
    def aging_level(self):
        days = self.days_on_site
        if days is None:
            return 'normal'
        if days >= 60:
            return 'critical'
        if days >= 30:
            return 'warning'
        return 'normal'

    @property
    def completion_percentage(self):
        milestones = [
            self.date_arrived, self.shopping_pkg_received,
            self.inbound_inspection, self.estimate_sent,
            self.estimate_approved, self.work_order_created,
            self.repair_start_date, self.repair_completed_date,
            self.projected_outbound, self.outbound_inspection,
            self.dispo_requested, self.dispo_received,
            self.final_estimate_approved
        ]
        filled = sum(1 for d in milestones if d is not None)
        return round((filled / len(milestones)) * 100)

    @property
    def current_owner(self):
        cs_pre    = ['Inbounded','Waiting Inspection','Waiting Estimate','Waiting Approval']
        scheduler = ['Work Order Created','Scheduled','Waiting Cleaning','In Cleaning',
                     'Cleaned','Waiting Material','In Repair','Repair Complete']
        cs_post   = ['Waiting Outbound Inspection','Waiting Dispo','Dispo Received',
                     'Billed','Completed']
        if self.status in cs_pre or self.status in cs_post:
            return 'Customer Service'
        return 'Scheduler'


# ─────────────────────────────────────────────
# MONTHLY TARGET
# ─────────────────────────────────────────────
class MonthlyTarget(db.Model):
    __tablename__ = 'monthly_targets'
    id              = db.Column(db.Integer, primary_key=True)
    location_id     = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    month           = db.Column(db.Integer, nullable=False)
    year            = db.Column(db.Integer, nullable=False)
    car_target      = db.Column(db.Integer, default=40)
    revenue_target  = db.Column(db.Float, default=0.0)
    created_by      = db.Column(db.String(100))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# SPOT ASSIGNMENTS
# ─────────────────────────────────────────────
class SpotAssignment(db.Model):
    __tablename__ = 'spot_assignments'
    id              = db.Column(db.Integer, primary_key=True)
    spot_id         = db.Column(db.Integer, db.ForeignKey('spots.id'),       nullable=False)
    work_order_id   = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)

    sow_type        = db.Column(db.String(50))
    technician      = db.Column(db.String(100))
    estimated_hours = db.Column(db.Float, default=0.0)
    actual_hours    = db.Column(db.Float, default=0.0)
    pct_complete    = db.Column(db.Integer, default=0)
    target_date     = db.Column(db.Date)
    status          = db.Column(db.String(50), default='Under Repair')
    hold_reason     = db.Column(db.String(255))
    notes           = db.Column(db.Text)
    scheduled_start_date = db.Column(db.Date)
    scheduled_end_date   = db.Column(db.Date)
    is_active       = db.Column(db.Boolean, default=True)
    assigned_at     = db.Column(db.DateTime, default=datetime.utcnow)
    cleared_at      = db.Column(db.DateTime)
    assigned_by     = db.Column(db.String(100))
    updated_by      = db.Column(db.String(100))
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def days_in_spot(self):
        if self.assigned_at:
            return (datetime.utcnow() - self.assigned_at).days
        return 0


# ─────────────────────────────────────────────
# YARD CARS
# ─────────────────────────────────────────────
class YardCar(db.Model):
    __tablename__ = 'yard_cars'
    id              = db.Column(db.Integer, primary_key=True)
    work_order_id   = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    track_id        = db.Column(db.Integer, db.ForeignKey('yard_tracks.id'), nullable=False)
    yard_status     = db.Column(db.String(50), default='Just Inbounded')
    sow_notes       = db.Column(db.String(255))
    comments        = db.Column(db.Text)
    return_location = db.Column(db.String(255))
    is_active       = db.Column(db.Boolean, default=True)
    entered_at      = db.Column(db.DateTime, default=datetime.utcnow)
    exited_at       = db.Column(db.DateTime)
    updated_by      = db.Column(db.String(100))


# ─────────────────────────────────────────────
# CLEANING ENTRIES
# ─────────────────────────────────────────────
class CleaningEntry(db.Model):
    __tablename__ = 'cleaning_entries'
    id              = db.Column(db.Integer, primary_key=True)
    work_order_id   = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    location_id     = db.Column(db.Integer, db.ForeignKey('locations.id'),   nullable=False)
    rack_position   = db.Column(db.Integer)
    scheduled_date  = db.Column(db.Date)
    cleaning_status = db.Column(db.String(50), default='Scheduled')
    material_notes  = db.Column(db.String(255))
    notes           = db.Column(db.Text)
    cleaned_at      = db.Column(db.DateTime)
    updated_by      = db.Column(db.String(100))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────
# SCHEDULE ENTRIES
# ─────────────────────────────────────────────
class ScheduleEntry(db.Model):
    __tablename__ = 'schedule_entries'
    id              = db.Column(db.Integer, primary_key=True)
    work_order_id   = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    location_id     = db.Column(db.Integer, db.ForeignKey('locations.id'),   nullable=False)
    month           = db.Column(db.Integer, nullable=False)
    year            = db.Column(db.Integer, nullable=False)
    target_week     = db.Column(db.Integer)
    target_date     = db.Column(db.Date)
    schedule_status = db.Column(db.String(50), default='Scheduled')
    rev_per_hour    = db.Column(db.Float, default=0.0)
    priority_score  = db.Column(db.Float, default=0.0)
    notes           = db.Column(db.Text)
    scheduled_by    = db.Column(db.String(100))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────
# COMMENTS
# ─────────────────────────────────────────────
class Comment(db.Model):
    __tablename__ = 'comments'
    id              = db.Column(db.Integer, primary_key=True)
    work_order_id   = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    author          = db.Column(db.String(100), nullable=False)
    role            = db.Column(db.String(50))
    body            = db.Column(db.Text, nullable=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# ACTIVITY LOG
# ─────────────────────────────────────────────
class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id              = db.Column(db.Integer, primary_key=True)
    work_order_id   = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    user            = db.Column(db.String(100), nullable=False)
    role            = db.Column(db.String(50))
    action          = db.Column(db.String(100))
    field_name      = db.Column(db.String(100))
    old_value       = db.Column(db.String(255))
    new_value       = db.Column(db.String(255))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    role        = db.Column(db.String(50),  nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


# ─────────────────────────────────────────────
# GANTT MARKS  — one record per spot/day booking
# ─────────────────────────────────────────────
class GanttMark(db.Model):
    __tablename__ = 'gantt_marks'
    __table_args__ = (
        db.UniqueConstraint('spot_id', 'mark_date', name='uq_spot_date'),
    )

    id            = db.Column(db.Integer, primary_key=True)
    spot_id       = db.Column(db.Integer, db.ForeignKey('spots.id'),       nullable=False)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    location_id   = db.Column(db.Integer, db.ForeignKey('locations.id'),   nullable=False)
    mark_date     = db.Column(db.Date, nullable=False)
    created_by    = db.Column(db.String(100))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    spot       = db.relationship('Spot',      backref='gantt_marks', lazy=True)
    work_order = db.relationship('WorkOrder', backref='gantt_marks', lazy=True)