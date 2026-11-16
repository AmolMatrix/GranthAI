"""
GranthAI - Software-Only Smart Library Web Application
--------------------------------------------------------
Run locally:
    python app.py

Then open:
    http://127.0.0.1:5000/

First run automatically creates the database.
"""

import os 

from flask import Flask  #A framework provides predefined tools, structures and functionality so developers don't have to build everything from scratch.
from extensions import db
from routes.auth import auth_bp #authentication 6 | Authorization :	Checking WHAT you are allowed to access
from routes.student import student_bp  #handle everything that student can do
from routes.librarian import librarian_bp

def create_app():
    app = Flask(__name__)   #creates the actual flask web application object

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///granthai.db').replace('postgres://', 'postgresql://', 1)
    # Tells flask where to store your data. if URL have then store else granthai.db

    # Secret key:
    # Render will provide SECRET_KEY through an environment variable.
    # The fallback is only for local development.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'local-demo-key-change-before-deployment')
    # Sets a secret password that flask uses to keep user login session and cookies secure.

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  #turn off extra tracking SQLALCHEMY features to save memory and and prevent warnign message

    # Initialize database : connect database to app
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)   #visitors can actually take to them all
    app.register_blueprint(librarian_bp)

    # Create database tables and seed initial data
    with app.app_context():
        db.create_all()

        from seed_data import seed_if_empty
        seed_if_empty()  # Fill sample book if empty

    return app   # hand back the fully configured website


# Create Flask application
app = create_app()


if __name__ == '__main__':
    # Local development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('FLASK_DEBUG', '0') == '1'
    )
