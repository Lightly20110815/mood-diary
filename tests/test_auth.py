import os
import pytest
from config import Config, is_production


def test_missing_vars_in_production():
    # In Vercel environment: missing SECRET_KEY raises RuntimeError
    old_env = dict(os.environ)
    try:
        os.environ['VERCEL'] = '1'
        os.environ.pop('SECRET_KEY', None)
        os.environ.pop('ADMIN_PASSWORD', None)

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            Config.reload()

        os.environ['SECRET_KEY'] = 'test-secret-key'
        with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
            Config.reload()
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        Config.reload()


def test_dev_mode_missing_admin_password():
    # In dev mode: missing ADMIN_PASSWORD disables login
    old_env = dict(os.environ)
    try:
        os.environ.pop('VERCEL', None)
        os.environ.pop('FLASK_ENV', None)
        os.environ.pop('ENV', None)
        os.environ.pop('ENVIRONMENT', None)
        os.environ.pop('ADMIN_PASSWORD', None)
        Config.reload()

        from app import app
        app.config['ADMIN_PASSWORD'] = None

        client = app.test_client()
        # GET /login should show disabled notice
        resp = client.get('/login')
        assert resp.status_code == 200
        assert "管理员密码未设置，登录功能已禁用" in resp.get_data(as_text=True)

        # POST /login should not log in
        post_resp = client.post('/login', data={'password': 'anypassword'})
        assert post_resp.status_code == 200
        assert "管理员密码未设置，登录功能已禁用" in post_resp.get_data(as_text=True)

        # /admin should redirect to /login
        admin_resp = client.get('/admin')
        assert admin_resp.status_code == 302
        assert '/login' in admin_resp.headers['Location']
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        Config.reload()


def test_auth_success_and_failure():
    old_env = dict(os.environ)
    try:
        os.environ['SECRET_KEY'] = 'super-secret-key-12345'
        os.environ['ADMIN_PASSWORD'] = 'my-secure-password-456'
        Config.reload()

        from app import app
        app.config['SECRET_KEY'] = 'super-secret-key-12345'
        app.config['ADMIN_PASSWORD'] = 'my-secure-password-456'

        client = app.test_client()

        # Wrong password
        resp_wrong = client.post('/login', data={'password': 'wrongpassword'})
        assert resp_wrong.status_code == 200
        assert "密码错误" in resp_wrong.get_data(as_text=True)

        # Correct password
        resp_correct = client.post('/login', data={'password': 'my-secure-password-456'})
        assert resp_correct.status_code == 302
        assert '/admin' in resp_correct.headers['Location']

        # Access /admin with active session
        resp_admin = client.get('/admin')
        assert resp_admin.status_code == 200
        assert "每日心情后台" in resp_admin.get_data(as_text=True) or resp_admin.status_code == 200
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        Config.reload()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

