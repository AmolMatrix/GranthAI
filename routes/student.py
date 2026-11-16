from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Book, SearchHistory, Announcement, Reservation, IssueRecord, User
from decorators import role_required
from recommender import rank_by_similarity

student_bp = Blueprint('student', __name__, url_prefix='/student')

DEPARTMENTS = [
    'Computer Engineering', 'Mechanical Engineering', 'Electrical Engineering',
    'Civil Engineering', 'Electronics Engineering', 'Pharmacy', 'Diploma',
    'Management',
]


def _current_user():
    return db.session.get(User, session['user_id'])


@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    user = _current_user()

    recent_books = Book.query.filter_by(item_type='book').order_by(Book.added_on.desc()).limit(6).all()
    magazines = Book.query.filter_by(item_type='magazine').order_by(Book.added_on.desc()).limit(6).all()
    trending = Book.query.filter_by(item_type='book').order_by(Book.view_count.desc()).limit(6).all()
    announcements = Announcement.query.order_by(Announcement.posted_on.desc()).limit(5).all()

    # "Recommended for you" - built from this student's last 5 search queries
    recent_queries = (
        SearchHistory.query.filter_by(student_id=user.id)
        .order_by(SearchHistory.searched_on.desc())
        .limit(5)
        .all()
    )
    recommendations = []
    if recent_queries:
        combined_query = ' '.join(q.search_query for q in recent_queries)
        all_books = Book.query.filter_by(item_type='book').all()
        documents = [(b.id, f"{b.title} {b.content or ''}") for b in all_books]
        ranked = rank_by_similarity(combined_query, documents, top_n=6)
        book_map = {b.id: b for b in all_books}
        recommendations = [book_map[bid] for bid, _ in ranked if bid in book_map]

    my_issued = (
        IssueRecord.query.filter_by(student_id=user.id, returned_on=None)
        .join(Book).order_by(IssueRecord.issued_on.desc()).all()
    )

    return render_template(
        'student/dashboard.html',
        user=user,
        recent_books=recent_books,
        magazines=magazines,
        trending=trending,
        announcements=announcements,
        recommendations=recommendations,
        my_issued=my_issued,
        departments=DEPARTMENTS,
    )


@student_bp.route('/search')
@role_required('student')
def search():
    user = _current_user()
    query = request.args.get('q', '').strip()
    department = request.args.get('department', '').strip()
    include_magazines = request.args.get('magazines') == 'on'

    if not query and not department:
        return redirect(url_for('student.dashboard'))

    base_query = Book.query
    if not include_magazines:
        base_query = base_query.filter_by(item_type='book')
    if department:
        base_query = base_query.filter_by(department=department)

    candidate_books = base_query.all()

    title_matches = []
    concept_matches = []

    if query:
        # log this search for history + future recommendations
        db.session.add(SearchHistory(student_id=user.id, search_query=query, department_filter=department))
        db.session.commit()

        title_matches = [b for b in candidate_books if query.lower() in b.title.lower()]

        documents = [(b.id, f"{b.title} {b.author or ''} {b.content or ''}") for b in candidate_books]
        ranked = rank_by_similarity(query, documents, top_n=8)
        book_map = {b.id: b for b in candidate_books}
        concept_matches = [(book_map[bid], score) for bid, score in ranked if bid in book_map]
    else:
        # department filter only, no text query - just list the department's catalog
        title_matches = candidate_books

    return render_template(
        'student/search_results.html',
        query=query,
        department=department,
        departments=DEPARTMENTS,
        title_matches=title_matches,
        concept_matches=concept_matches,
    )


@student_bp.route('/book/<int:book_id>')
@role_required('student')
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    book.view_count = (book.view_count or 0) + 1
    db.session.commit()

    user = _current_user()
    already_reserved = Reservation.query.filter_by(
        book_id=book.id, student_id=user.id, status='waiting'
    ).first()

    # "Similar books" - concept search using this book's own content as the query
    similar_ranked = rank_by_similarity(
        f"{book.title} {book.content or ''}",
        [(b.id, f"{b.title} {b.content or ''}") for b in Book.query.filter(
            Book.id != book.id, Book.item_type == book.item_type
        ).all()],
        top_n=4,
    )
    similar_books = [db.session.get(Book, bid) for bid, _ in similar_ranked]

    return render_template(
        'student/book_detail.html',
        book=book,
        already_reserved=already_reserved,
        similar_books=similar_books,
    )


@student_bp.route('/reserve/<int:book_id>', methods=['POST'])
@role_required('student')
def reserve(book_id):
    user = _current_user()
    book = db.get_or_404(Book, book_id)

    existing = Reservation.query.filter_by(book_id=book.id, student_id=user.id, status='waiting').first()
    if existing:
        flash('You are already on the waitlist for this item.')
    else:
        db.session.add(Reservation(book_id=book.id, student_id=user.id))
        db.session.commit()
        flash(f'You have been added to the waitlist for "{book.title}". You will be notified when a copy is free.')

    return redirect(url_for('student.book_detail', book_id=book.id))


@student_bp.route('/history')
@role_required('student')
def history():
    user = _current_user()
    past_searches = (
        SearchHistory.query.filter_by(student_id=user.id)
        .order_by(SearchHistory.searched_on.desc())
        .limit(50)
        .all()
    )
    past_issues = (
        IssueRecord.query.filter_by(student_id=user.id)
        .join(Book).order_by(IssueRecord.issued_on.desc()).all()
    )
    return render_template('student/history.html', past_searches=past_searches, past_issues=past_issues)
