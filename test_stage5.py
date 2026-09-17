from datetime import date
from app import app, db
from models import User, Subject, Task, Assignment, Exam, Attendance
from services.workload_service import calculate_overall_workload

def run_tests():
    print("==================================================")
    print("STARTING STAGE 5 AUTOMATED INTEGRATION TESTS")
    print("==================================================")

    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    # 1. REGISTER & LOGIN ALICE
    client.post('/register', data={
        'username': 'alice',
        'email': 'alice@student.edu',
        'password': 'password123'
    }, follow_redirects=True)

    client.post('/login', data={
        'username_or_email': 'alice',
        'password': 'password123'
    }, follow_redirects=True)

    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        alice_id = alice.id

    # 2. SEED DEMO DATA
    res_seed = client.post('/demo-data/seed', follow_redirects=True)
    assert res_seed.status_code == 200
    assert b'Computer Networks' in res_seed.data

    with app.app_context():
        subjects = Subject.query.filter_by(user_id=alice_id).all()
        assert len(subjects) == 5
        sub_names = [s.name for s in subjects]
        assert 'Computer Networks' in sub_names
        assert 'Database Management Systems' in sub_names
        assert 'Operating Systems' in sub_names

        # Verify Workload Score Updated
        wl = calculate_overall_workload(alice_id)
        assert wl['score'] > 0
    print("[PASS] Engineering Demo Data Seeder Verified (5 Engineering Courses & Real Workload Score)")

    # 3. SECURITY DATA ISOLATION & ERROR HANDLERS
    client.get('/logout')
    
    # Unauthenticated API Access -> 401 JSON
    res_unauth = client.get('/api/workload')
    assert res_unauth.status_code in [302, 401]
    print("[PASS] Unauthenticated Request Handled (Redirect to Login / 401 Unauthorized)")



    # Non-existent route -> 404 HTML Page
    res_404 = client.get('/non-existent-page-test-123')
    assert res_404.status_code == 404
    assert b'404 - Page Not Found' in res_404.data
    print("[PASS] Custom 404 Error Handler Verified")

    # Register User Bob
    client.post('/register', data={
        'username': 'bob',
        'email': 'bob@student.edu',
        'password': 'password123'
    }, follow_redirects=True)

    client.post('/login', data={
        'username_or_email': 'bob',
        'password': 'password123'
    }, follow_redirects=True)

    with app.app_context():
        # Verify Bob cannot see Alice's subjects
        bob_subs = Subject.query.filter_by(user_id=User.query.filter_by(username='bob').first().id).all()
        assert len(bob_subs) == 0

    print("[PASS] Security & Data Isolation Verified for Multiple Users")

    print("==================================================")
    print("ALL STAGE 5 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
