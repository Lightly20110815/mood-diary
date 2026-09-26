import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def is_production():
    return bool(
        os.getenv('VERCEL')
        or os.getenv('FLASK_ENV') == 'production'
        or os.getenv('ENV') == 'production'
        or os.getenv('ENVIRONMENT') == 'production'
    )


def _get_database_uri():
    uri = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    if uri:
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        return uri
    return 'sqlite:///moods.db'


def _get_secret_key():
    secret = os.getenv('SECRET_KEY')
    if secret:
        return secret
    if is_production():
        raise RuntimeError("生产环境（或 Vercel）必须配置环境变量 'SECRET_KEY'，未设置将拒绝启动。")
    return secrets.token_hex(32)


def _get_admin_password():
    password = os.getenv('ADMIN_PASSWORD')
    if password:
        return password
    if is_production():
        raise RuntimeError("生产环境（或 Vercel）必须配置环境变量 'ADMIN_PASSWORD'，未设置将拒绝启动。")
    return None


class Config:
    SECRET_KEY = _get_secret_key()
    ADMIN_PASSWORD = _get_admin_password()
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }

    @classmethod
    def reload(cls):
        cls.SECRET_KEY = _get_secret_key()
        cls.ADMIN_PASSWORD = _get_admin_password()
        cls.SQLALCHEMY_DATABASE_URI = _get_database_uri()
        return cls
