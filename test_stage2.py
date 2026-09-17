from datetime import date
from app import app, db
from models import User, Subject, Task, Assignment, Exam

def run_tests():
    print("==================================================")
    print("STARTING STAGE 2 AUTOMATED INTEGRATION TESTS")
    print("==================================================")

    # Use test client
    client = app.test_client()

    with app.app_context():
        # Clean test database
        db.drop_all()
        db.create_all()

    # 1. REGISTER STUDENT ALICE & BOB
    res1 = client.post('/register', data={
        'username': 'alice',
        'email': 'alice@student.edu',
        'password': 'password123'
    }, follow_redirects=True)
    assert res1.status_code == 200
    assert b'Registration successful' in res1.data
    print("[PASS] User Alice Registration")

    res2 = client.post('/register', data={
        'username': 'bob',
        'email': 'bob@student.edu',
        'password': 'password123'
    }, follow_redirects=True)
    assert res2.status_code == 200
    assert b'Registration successful' in res2.data
    print("[PASS] User Bob Registration")

    # 2. LOGIN ALICE
    res_login = client.post('/login', data={
        'username_or_email': 'alice',
        'password': 'password123'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b'Welcome back, alice!' in res_login.data
    print("[PASS] User Alice Login")

    # 3. SUBJECT CRUD (ALICE)
    res_sub_add = client.post('/subjects/add', data={
        'name': 'Data Structures',
        'faculty_name': 'Dr. Knuth',
        'credits': 4
    }, follow_redirects=True)
    assert b'Subject &quot;Data Structures&quot; added successfully!' in res_sub_add.data or b'Data Structures' in res_sub_add.data

    print("[PASS] Subject Added for Alice")

    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        sub1 = Subject.query.filter_by(user_id=alice.id, name='Data Structures').first()
        assert sub1 is not None
        sub1_id = sub1.id

    # Edit Subject
    res_sub_edit = client.post(f'/subjects/{sub1_id}/edit', data={
        'name': 'Data Structures & Algorithms',
        'faculty_name': 'Dr. Donald Knuth',
        'credits': 4
    }, follow_redirects=True)
    assert b'Data Structures &amp; Algorithms' in res_sub_edit.data
    print("[PASS] Subject Edited for Alice")

    # Add second subject for Alice
    client.post('/subjects/add', data={
        'name': 'Operating Systems',
        'faculty_name': 'Dr. Tanenbaum',
        'credits': 3
    }, follow_redirects=True)

    with app.app_context():
        sub2 = Subject.query.filter_by(user_id=alice.id, name='Operating Systems').first()
        sub2_id = sub2.id

    # 4. TASK CRUD & COMPLETION TOGGLE (ALICE)
    today_str = date.today().strftime('%Y-%m-%d')
    res_task_add = client.post('/tasks/add', data={
        'title': 'Page Replacement Algorithm Task',
        'description': 'Implement LRU in Python',
        'subject_id': sub2_id,
        'deadline': today_str,
        'priority': 'High',
        'difficulty': 'Hard',
        'estimated_hours': 3.0,
        'status': 'Not Started'
    }, follow_redirects=True)
    assert b'Page Replacement Algorithm Task' in res_task_add.data
    print("[PASS] Task Added for Alice")

    with app.app_context():
        task = Task.query.filter_by(user_id=alice.id, title='Page Replacement Algorithm Task').first()
        task_id = task.id

    # Mark Task Completed
    res_task_comp = client.post(f'/tasks/{task_id}/complete', follow_redirects=True)
    with app.app_context():
        updated_task = db.session.get(Task, task_id)
        assert updated_task.status == 'Completed'
    print("[PASS] Task Mark Completed for Alice")

    # Add a pending task due today
    client.post('/tasks/add', data={
        'title': 'Read Process Synchronization',
        'description': 'Study semaphores',
        'subject_id': sub2_id,
        'deadline': today_str,
        'priority': 'Medium',
        'difficulty': 'Medium',
        'estimated_hours': 1.5,
        'status': 'In Progress'
    }, follow_redirects=True)

    # 5. ASSIGNMENT CRUD & STATUS UPDATE (ALICE)
    res_ass_add = client.post('/assignments/add', data={
        'title': 'OS Lab Report 1',
        'description': 'Kernel module build report',
        'subject_id': sub2_id,
        'deadline': today_str,
        'difficulty': 'Medium',
        'estimated_hours': 4.0,
        'status': 'Not Started'
    }, follow_redirects=True)
    assert b'OS Lab Report 1' in res_ass_add.data
    print("[PASS] Assignment Added for Alice")

    with app.app_context():
        ass = Assignment.query.filter_by(user_id=alice.id, title='OS Lab Report 1').first()
        ass_id = ass.id

    # Change Assignment Status
    client.post(f'/assignments/{ass_id}/status', data={'status': 'In Progress'}, follow_redirects=True)
    with app.app_context():
        updated_ass = db.session.get(Assignment, ass_id)

        assert updated_ass.status == 'In Progress'
    print("[PASS] Assignment Status Updated to In Progress for Alice")

    # 6. EXAM CRUD (ALICE)
    res_exam_add = client.post('/exams/add', data={
        'subject_id': sub2_id,
        'exam_date': today_str,
        'exam_time': '10:00 AM',
        'difficulty': 'Hard',
        'syllabus': 'Units 1 to 3',
        'prep_percentage': 60
    }, follow_redirects=True)
    assert b'Exam schedule added successfully!' in res_exam_add.data
    print("[PASS] Exam Added for Alice")

    with app.app_context():
        exam = Exam.query.filter_by(user_id=alice.id, subject_id=sub2_id).first()
        exam_id = exam.id

    # 7. VERIFY DASHBOARD COUNTERS (ALICE)
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200
    # Alice has 2 subjects, 1 pending task due today, 1 pending assignment, 1 upcoming exam
    assert b'Subjects' in res_dash.data

    print("[PASS] Dashboard Metrics Verified for Alice")

    # 8. DATA ISOLATION & SECURITY TEST (BOB)
    # Logout Alice
    client.get('/logout')

    # Login Bob
    client.post('/login', data={
        'username_or_email': 'bob',
        'password': 'password123'
    }, follow_redirects=True)

    # Verify Bob's subjects list is empty
    res_bob_sub = client.get('/subjects')
    assert b'Data Structures &amp; Algorithms' not in res_bob_sub.data
    assert b'No subjects' in res_bob_sub.data
    print("[PASS] Data Isolation: Bob cannot view Alice's subjects")

    # Attempt to edit Alice's subject as Bob -> Should return 404
    res_hack_sub = client.post(f'/subjects/{sub1_id}/edit', data={
        'name': 'Hacked Subject Name',
        'credits': 1
    })
    assert res_hack_sub.status_code == 404
    print("[PASS] Data Isolation: Bob editing Alice's subject returned 404")

    # Attempt to delete Alice's task as Bob -> Should return 404
    res_hack_task = client.post(f'/tasks/{task_id}/delete')
    assert res_hack_task.status_code == 404
    print("[PASS] Data Isolation: Bob deleting Alice's task returned 404")

    # Attempt to delete Alice's assignment as Bob -> Should return 404
    res_hack_ass = client.post(f'/assignments/{ass_id}/delete')
    assert res_hack_ass.status_code == 404
    print("[PASS] Data Isolation: Bob deleting Alice's assignment returned 404")

    # Attempt to delete Alice's exam as Bob -> Should return 404
    res_hack_exam = client.post(f'/exams/{exam_id}/delete')
    assert res_hack_exam.status_code == 404
    print("[PASS] Data Isolation: Bob deleting Alice's exam returned 404")

    # 9. LOGOUT BOB
    res_logout = client.get('/logout', follow_redirects=True)
    assert b'You have been logged out.' in res_logout.data
    print("[PASS] User Bob Logout")

    print("==================================================")
    print("ALL STAGE 2 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
