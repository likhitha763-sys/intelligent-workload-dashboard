import unittest
from app import app
from config import Config
from models.models import db, User

class BrowserStudentVerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.from_object(Config)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_browserstudent_flow(self):
        username = "browserstudent"
        email = "browserstudent@gmail.com"
        password = "Browser@12345"

        # Cleanup browserstudent if exists
        existing = User.query.filter(
            (db.func.lower(User.username) == username.lower()) | 
            (db.func.lower(User.email) == email.lower())
        ).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        print("\n--- STAGE 5B REAL BROWSER SIMULATION ---")
        # D. Register brand new user
        print("D. Registering browserstudent...")
        reg_res = self.client.post('/register', data={
            'username': username,
            'email': email,
            'password': password
        }, follow_redirects=True)
        
        # E. Verify registration success
        print("E. Verifying registration flash & DB insertion...")
        self.assertEqual(reg_res.status_code, 200)
        self.assertIn(b"Registration successful", reg_res.data)

        user_in_db = User.query.filter(db.func.lower(User.username) == username).first()
        self.assertIsNotNone(user_in_db)
        print(f"   [DB VERIFIED] User ID: {user_in_db.id} | Username: {user_in_db.username} | Email: {user_in_db.email} | Hash Valid: {user_in_db.check_password(password)}")

        # F. Login using username: browserstudent / Browser@12345
        print("F. Logging in with username 'browserstudent'...")
        login_u_res = self.client.post('/login', data={
            'username_or_email': username,
            'password': password
        }, follow_redirects=False)

        # G. Verify successful Dashboard redirect
        print("G. Verifying redirect to /dashboard...")
        self.assertEqual(login_u_res.status_code, 302)
        self.assertIn('/dashboard', login_u_res.headers['Location'])

        dash_res = self.client.get('/dashboard')
        self.assertIn(b"browserstudent", dash_res.data)
        print("   [SUCCESS] Logged in by username successfully!")

        # H. Logout
        print("H. Logging out...")
        self.client.get('/logout', follow_redirects=True)

        # I. Login using email: browserstudent@gmail.com / Browser@12345
        print("I. Logging in with email 'browserstudent@gmail.com'...")
        login_e_res = self.client.post('/login', data={
            'username_or_email': email,
            'password': password
        }, follow_redirects=False)

        # J. Verify successful Dashboard redirect again
        print("J. Verifying redirect to /dashboard for email login...")
        self.assertEqual(login_e_res.status_code, 302)
        self.assertIn('/dashboard', login_e_res.headers['Location'])
        print("   [SUCCESS] Logged in by email successfully!")

        # K. Try: browserstudent / WrongPassword
        print("K. Testing wrong password rejection...")
        self.client.get('/logout', follow_redirects=True)
        wrong_p_res = self.client.post('/login', data={
            'username_or_email': username,
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertIn(b"Invalid username/email or password", wrong_p_res.data)
        print("   [SUCCESS] Wrong password correctly rejected with alert message!")

if __name__ == '__main__':
    unittest.main()
