from datetime import datetime
from utils import utcnow
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Book, Announcement, Reservation, IssueRecord, User
from decorators import role_required

librarian_bp = Blueprint('librarian', __name__, url_prefix='/librarian')

DEPARTMENTS = [
    'Computer Engineering', 'Mechanical Engineering', 'Electrical Engineering',
    'Civil Engineering', 'Electronics Engineering', 'Pharmacy', 'Diploma',
    'Management',
]


@librarian_bp.route('/dashboard')
@role_required('librarian')
def dashboard():
    total_books = Book.query.filter_by(item_type='book').count()
    total_magazines = Book.query.filter_by(item_type='magazine').count()
    total_students = User.query.filter_by(role='student').count()
    low_stock = Book.query.filter(Book.item_type == 'book', Book.available_copies == 0).all()
    pending_reservations = Reservation.query.filter_by(status='waiting').count()
    recent_books = Book.query.order_by(Book.added_on.desc()).limit(6).all()
    currently_issued = IssueRecord.query.filter_by(returned_on=None).count()

    return render_template(
        'librarian/dashboard.html',
        total_books=total_books,
        total_magazines=total_magazines,
        total_students=total_students,
        low_stock=low_stock,
        pending_reservations=pending_reservations,
        recent_books=recent_books,
        currently_issued=currently_issued,
    )


@librarian_bp.route('/books')
@role_required('librarian')
def books_list():
    department = request.args.get('department', '')
    item_type = request.args.get('item_type', '')
    q = request.args.get('q', '')

    query = Book.query
    if department:
        query = query.filter_by(department=department)
    if item_type:
        query = query.filter_by(item_type=item_type)
    if q:
        query = query.filter(Book.title.ilike(f'%{q}%'))

    books = query.order_by(Book.added_on.desc()).all()
    return render_template('librarian/books_list.html', books=books, departments=DEPARTMENTS,
                            department=department, item_type=item_type, q=q)


@librarian_bp.route('/books/add', methods=['GET', 'POST'])
@role_required('librarian')
def add_book():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        try:
            copies = int(request.form.get('total_copies') or 1)
        except (TypeError, ValueError):
            copies = 0
        if not title or copies < 1:
            flash('Enter a book title and a valid copy count (at least 1).')
            return redirect(url_for('librarian.add_book'))
        book = Book(
            title=title,
            author=request.form.get('author'),
            department=request.form.get('department'),
            level=request.form.get('level'),
            item_type=request.form.get('item_type', 'book'),
            content=request.form.get('content'),
            total_copies=copies,
            available_copies=copies,
            shelf_location=request.form.get('shelf_location'),
        )
        db.session.add(book)
        db.session.commit()
        flash(f'"{book.title}" added to the catalog.')
        return redirect(url_for('librarian.books_list'))

    return render_template('librarian/book_form.html', departments=DEPARTMENTS, book=None)


@librarian_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@role_required('librarian')
def edit_book(book_id):
    book = db.get_or_404(Book, book_id)

    if request.method == 'POST':
        old_total = book.total_copies
        try:
            new_total = int(request.form.get('total_copies') or 1)
        except (TypeError, ValueError):
            new_total = 0
        title = request.form.get('title', '').strip()
        if not title or new_total < 1:
            flash('Enter a book title and a valid copy count (at least 1).')
            return redirect(url_for('librarian.edit_book', book_id=book.id))
        issued_count = old_total - book.available_copies
        if new_total < issued_count:
            flash(f'Cannot set copies below the {issued_count} copies currently issued.')
            return redirect(url_for('librarian.edit_book', book_id=book.id))

        book.title = title
        book.author = request.form.get('author')
        book.department = request.form.get('department')
        book.level = request.form.get('level')
        book.item_type = request.form.get('item_type', 'book')
        book.content = request.form.get('content')
        book.total_copies = new_total
        book.available_copies = max(0, new_total - issued_count)
        book.shelf_location = request.form.get('shelf_location')

        db.session.commit()
        flash(f'"{book.title}" updated.')
        return redirect(url_for('librarian.books_list'))

    return render_template('librarian/book_form.html', departments=DEPARTMENTS, book=book)


@librarian_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@role_required('librarian')
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Item removed from the catalog.')
    return redirect(url_for('librarian.books_list'))


@librarian_bp.route('/issue', methods=['GET', 'POST'])
@role_required('librarian')
def issue_book():
    if request.method == 'POST':
        student_email = request.form.get('student_email', '').strip().lower()
        book_id_raw = request.form.get('book_id', '')

        if not book_id_raw or not book_id_raw.isdigit():
            flash('Please select a valid book to issue.')
            return redirect(url_for('librarian.issue_book'))

        book_id = int(book_id_raw)

        student = User.query.filter_by(email=student_email, role='student').first()
        book = db.session.get(Book, book_id)

        if not student:
            flash('No student found with that email.')
        elif not book:
            flash('Book not found.')
        elif book.available_copies < 1:
            flash(f'No copies of "{book.title}" are currently available.')
        else:
            book.available_copies -= 1
            db.session.add(IssueRecord(book_id=book.id, student_id=student.id))
            db.session.commit()
            flash(f'"{book.title}" issued to {student.name}.')
        return redirect(url_for('librarian.issue_book'))

    active_issues = IssueRecord.query.filter_by(returned_on=None).join(Book).order_by(IssueRecord.issued_on.desc()).all()
    available_books = Book.query.filter(Book.item_type == 'book', Book.available_copies > 0).order_by(Book.title).all()
    return render_template('librarian/issue.html', active_issues=active_issues, available_books=available_books)


@librarian_bp.route('/return/<int:issue_id>', methods=['POST'])
@role_required('librarian')
def return_book(issue_id):
    record = db.get_or_404(IssueRecord, issue_id)
    if record.returned_on is None:
        record.returned_on = utcnow()
        record.book.available_copies = min(record.book.total_copies, record.book.available_copies + 1)
        db.session.commit()

        # auto-notify the oldest waitlisted student by marking the reservation
        # "fulfilled" so the librarian sees who to contact next
        next_in_line = (
            Reservation.query.filter_by(book_id=record.book_id, status='waiting')
            .order_by(Reservation.requested_on.asc())
            .first()
        )
        if next_in_line:
            next_in_line.status = 'fulfilled'
            db.session.commit()
            flash(f'"{record.book.title}" returned. {next_in_line.student.name} is next on the waitlist - notify them.')
        else:
            flash(f'"{record.book.title}" returned.')

    return redirect(url_for('librarian.issue_book'))


@librarian_bp.route('/reservations')
@role_required('librarian')
def reservations():
    waiting = Reservation.query.filter_by(status='waiting').order_by(Reservation.requested_on.asc()).all()
    fulfilled = Reservation.query.filter_by(status='fulfilled').order_by(Reservation.requested_on.desc()).limit(20).all()
    return render_template('librarian/reservations.html', waiting=waiting, fulfilled=fulfilled)


@librarian_bp.route('/announcements', methods=['GET', 'POST'])
@role_required('librarian')
def announcements():
    if request.method == 'POST':
        event_date_str = request.form.get('event_date', '')
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                event_date = None

        announcement = Announcement(
            title=request.form.get('title'),
            message=request.form.get('message'),
            event_date=event_date,
            posted_by=request.form.get('posted_by', 'Librarian'),
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement posted.')
        return redirect(url_for('librarian.announcements'))

    all_announcements = Announcement.query.order_by(Announcement.posted_on.desc()).all()
    return render_template('librarian/announcements.html', announcements=all_announcements)


@librarian_bp.route('/announcements/delete/<int:ann_id>', methods=['POST'])
@role_required('librarian')
def delete_announcement(ann_id):
    ann = db.get_or_404(Announcement, ann_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Announcement removed.')
    return redirect(url_for('librarian.announcements'))
