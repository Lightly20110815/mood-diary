import os
from dotenv import load_dotenv

load_dotenv()


def _get_database_uri():
    uri = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    if uri:
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        return uri
    return 'sqlite:///moods.db'


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
