"""Shared extension instances (kept separate from app.py to avoid circular imports)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
'''But what does this object actually do?

It provides functionality to:
1. Define database tables.
2. Insert records.
3. Retrieve records.
4. Update records.
5. Delete records.
6. Manage database sessions.'''

# This db is imported in app.py  used by model.py and app.py

'''website stores and retrieves information about students, books, reservations, and librarians.
1. First, what is SQLAlchemy?
Imagine your Granth AI website has a registration page.

A student enters:
- Name: Amol
- Email: amol@gmail.com
- Password: ********
You need to save this information in a database.

Normally, you could write SQL queries:
INSERT INTO users (name, email)
VALUES ('Amol', 'amol@gmail.com');


But SQLAlchemy allows you to perform database operations using Python code instead.

For example:
new_user = User(    name="Amol",    email="amol@gmail.com")db.session.add(new_user)db.session.commit()



See the difference?

Instead of writing SQL queries directly, you interact with database tables using Python objects.'''