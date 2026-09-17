import unittest
from app import app
from config import Config
from models.models import db, User

class RealBrowserFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        # Use main production/dev database configuration
        self.app.config.from_object(Config)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_reproduce_exact_user_registration_and_login(self):
        username = "teststudent"
        email = "teststudent@gmail.com"
        password = "Test@12345"

        # Clean existing teststudent if present
        existing = User.query.filter(
            (db.func.lower(User.username) == username.lower()) | 
            (db.func.lower(User.email) == email.lower())
        ).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        # Step 1: POST to /register
        print(f"\n[STEP 1] Registering {username} ({email})...")
        reg_res = self.client.post('/register', data={
            'username': username,
            'email': email,
            'password': password
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        # Step 2: Verify user exists in SQLite database
        print("[STEP 2] Querying database for inserted record...")
        db_user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.username, username)
        self.assertEqual(db_user.email, email)

        # Step 3: Verify password hash format
        print("[STEP 3] Verifying Werkzeug password hashing...")
        self.assertIsNotNone(db_user.password_hash)
        self.assertNotEqual(db_user.password_hash, password)
        self.assertTrue(db_user.check_password(password))

        # Step 4: Login with Username
        print("[STEP 4] Logging in with Username 'teststudent'...")
        login_username_res = self.client.post('/login', data={
            'username_or_email': username,
            'password': password
        }, follow_redirects=False)
        
        # Verify 302 redirect to dashboard
        self.assertEqual(login_username_res.status_code, 302)
        self.assertIn('/dashboard', login_username_res.headers['Location'])

        # Follow redirect and verify session dashboard content
        dash_res = self.client.get('/dashboard')
        self.assertIn(b"Dashboard", dash_res.data)
        self.assertIn(b"Logout", dash_res.data)
        print("[PASS] Username login & session redirect verified!")

        # Step 5: Logout
        print("[STEP 5] Logging out...")
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"You have been logged out", logout_res.data)

        # Step 6: Login with Email
        print("[STEP 6] Logging in with Email 'teststudent@gmail.com'...")
        login_email_res = self.client.post('/login', data={
            'username_or_email': email,
            'password': password
        }, follow_redirects=False)

        self.assertEqual(login_email_res.status_code, 302)
        self.assertIn('/dashboard', login_email_res.headers['Location'])
        print("[PASS] Email login & session redirect verified!")

        # Step 7: Test invalid password failure
        print("[STEP 7] Testing invalid password rejection...")
        self.client.get('/logout', follow_redirects=True)
        bad_pass_res = self.client.post('/login', data={
            'username_or_email': username,
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        self.assertIn(b"Invalid username/email or password", bad_pass_res.data)
        print("[PASS] Invalid password correctly rejected!")

if __name__ == '__main__':
    unittest.main()
