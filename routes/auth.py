from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)

DEPARTMENTS = [
    'Computer Engineering', 'Mechanical Engineering', 'Electrical Engineering',
    'Civil Engineering', 'Electronics Engineering', 'Pharmacy', 'Diploma',
    'Management',
]


@auth_bp.route('/')
def home():
    if 'user_id' in session:
        if session.get('role') == 'librarian':
            return redirect(url_for('librarian.dashboard'))
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """New student self-registration. Librarian accounts are provisioned
    separately (see seed_data.py) since a library only has a handful of
    librarian staff, unlike students who join continuously."""   # librarian account already create seperatly
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        department = request.form.get('department', '')

        if not name or not email or not password or len(password) < 6:
            flash('Enter your name, a valid Gmail address, and a password of at least 6 characters.')
            return render_template('auth/register.html', departments=DEPARTMENTS)

        if not email.endswith('@gmail.com') or email.count('@') != 1:
            flash('Please register with your Gmail address.')
            return render_template('auth/register.html', departments=DEPARTMENTS)

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please log in instead.')
            return redirect(url_for('auth.login'))

        student = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='student',
            department=department,
        )
        db.session.add(student)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', departments=DEPARTMENTS)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            if user.role == 'librarian':
                return redirect(url_for('librarian.dashboard'))
            return redirect(url_for('student.dashboard'))

        flash('Invalid email or password.')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))
