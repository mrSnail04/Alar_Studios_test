import os


DEBUG = True

CSRF_ENABLED = False

CSRF_SESSION_KEY = os.environ.get('CSRF_SESSION_KEY', "secret")

SECRET_KEY = os.environ.get('SECRET_KEY', "secret")

SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:123456@localhost:5432/test_db'
# DB_API_URI = os.environ['DATABASE_URL']
