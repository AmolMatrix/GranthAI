"""
Simple session-based auth helpers.

Deliberately not using Flask-Login here - a plain session dict is
enough for this project and keeps the dependency list minimal.

When a student tries to open the dashboard without logging in:
- flash() displays: Please log in to continue.
- redirect() sends the student to the login page.
- url_for() finds the login page's URL.
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.')
                return redirect(url_for('auth.login'))
            if session.get('role') != role:
                flash('You do not have access to that page.')
                return redirect(url_for('auth.login'))
            return view(*args, **kwargs)
        return wrapped
    return decorator
