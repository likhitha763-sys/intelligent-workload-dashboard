import unittest
from app import app
from models.models import db, User
from flask_login import current_user
import uuid

from config import TestConfig

class AuthFixTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.from_object(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_auth_complete_flow(self):
        unique_id = uuid.uuid4().hex[:6]
        username = f"TestUser_{unique_id}"
        email = f"user_{unique_id}@example.com"
        password = "SecurePassword123!"

        # 1. Registration
        reg_response = self.client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        self.assertEqual(reg_response.status_code, 200)

        # Check DB record
        user_in_db = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        self.assertIsNotNone(user_in_db)
        self.assertEqual(user_in_db.username, username)
        self.assertEqual(user_in_db.email, email)
        self.assertTrue(user_in_db.check_password(password))

        # 2. Duplicate registration checks
        dup_user_res = self.client.post('/register', data={
            'username': username.lower(), # Same username lowercased
            'email': f"different_{unique_id}@example.com",
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        self.assertIn(b"Username is already taken", dup_user_res.data)

        dup_email_res = self.client.post('/register', data={
            'username': f"Different_{unique_id}",
            'email': email.upper(), # Same email uppercased
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        self.assertIn(b"Email address is already registered", dup_email_res.data)

        # 3. Invalid password login
        bad_pass_res = self.client.post('/login', data={
            'username_or_email': username,
            'password': 'WrongPassword999'
        }, follow_redirects=True)
        self.assertIn(b"Invalid username/email or password", bad_pass_res.data)

        # 4. Login by exact Username
        login_exact_user = self.client.post('/login', data={
            'username_or_email': username,
            'password': password
        }, follow_redirects=True)
        self.assertIn(b"Dashboard", login_exact_user.data)
        self.assertIn(b"Logout", login_exact_user.data)

        # Logout
        self.client.get('/logout', follow_redirects=True)

        # 5. Login by lowercase Username
        login_lower_user = self.client.post('/login', data={
            'username_or_email': username.lower(),
            'password': password
        }, follow_redirects=True)
        self.assertIn(b"Dashboard", login_lower_user.data)

        # Logout
        self.client.get('/logout', follow_redirects=True)

        # 6. Login by uppercase Email
        login_upper_email = self.client.post('/login', data={
            'username_or_email': email.upper(),
            'password': password
        }, follow_redirects=True)
        self.assertIn(b"Dashboard", login_upper_email.data)

        # 7. Unauthenticated protected route access
        self.client.get('/logout', follow_redirects=True)
        protected_res = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(protected_res.status_code, 302)
        self.assertIn('/login', protected_res.headers['Location'])

if __name__ == '__main__':
    unittest.main()
