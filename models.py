"""
GranthAI - Database Models
---------------------------
Pure Flask-SQLAlchemy models. No external ML/data libraries are used
anywhere in this project (see recommender.py) so the whole app stays
compatible with any recent Python version, including 3.14.
"""
# Database tables: User, Book, SearchHistory, IssueRecord
from extensions import db
from utils import utcnow


class User(db.Model):
    """Single table for both students and librarians, split by `role`."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)  # Gmail, per registration
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'librarian'
    department = db.Column(db.String(80))  # only meaningful for students
    created_on = db.Column(db.DateTime, default=utcnow)

    search_history = db.relationship('SearchHistory', backref='student', cascade='all, delete-orphan', lazy=True)
    reservations = db.relationship('Reservation', backref='student', cascade='all, delete-orphan', lazy=True)
    issues = db.relationship('IssueRecord', backref='student', cascade='all, delete-orphan', lazy=True)

    @property
    def is_librarian(self):
        return self.role == 'librarian'

    @property
    def is_student(self):
        return self.role == 'student'


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(200))
    department = db.Column(db.String(80), index=True)  # e.g. Engineering, Pharmacy, Diploma, Management
    level = db.Column(db.String(20), default='Intermediate')  # Beginner / Intermediate / Advanced
    item_type = db.Column(db.String(20), default='book')  # 'book' or 'magazine'
    content = db.Column(db.Text)  # keywords / topics / description used for search
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    shelf_location = db.Column(db.String(80))  # e.g. "Rack E3, Shelf 2"
    view_count = db.Column(db.Integer, default=0)  # used for "Trending" widget
    added_on = db.Column(db.DateTime, default=utcnow, index=True)

    reservations = db.relationship('Reservation', backref='book', cascade='all, delete-orphan', lazy=True)
    issues = db.relationship('IssueRecord', backref='book', cascade='all, delete-orphan', lazy=True)

    @property
    def is_available(self):
        return self.available_copies > 0


class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_query = db.Column(db.String(250), nullable=False)
    department_filter = db.Column(db.String(80))
    searched_on = db.Column(db.DateTime, default=utcnow, index=True)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    event_date = db.Column(db.Date)  # optional - date of the event being announced
    posted_by = db.Column(db.String(120))
    posted_on = db.Column(db.DateTime, default=utcnow, index=True)


class Reservation(db.Model):
    """Waitlist entry for a book that has zero available copies."""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_on = db.Column(db.DateTime, default=utcnow)
    status = db.Column(db.String(20), default='waiting')  # waiting / fulfilled / cancelled


class IssueRecord(db.Model):
    """Tracks which student currently has (or previously had) which book."""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issued_on = db.Column(db.DateTime, default=utcnow)
    returned_on = db.Column(db.DateTime)  # NULL while still issued

    @property
    def is_returned(self):
        return self.returned_on is not None
