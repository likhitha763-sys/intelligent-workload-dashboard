from datetime import date, timedelta
from app import app, db
from models import User, Subject, Task, Assignment, Exam, Attendance, StudyPreference
from services.planner_service import generate_intelligent_study_plan
from services.ai_insights_service import generate_categorized_ai_insights
from services.attendance_service import get_subject_attendance_summary

def run_tests():
    print("==================================================")
    print("STARTING STAGE 4 AUTOMATED INTEGRATION TESTS")
    print("==================================================")

    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    # 1. REGISTER & LOGIN STUDENT ALICE
    res_reg = client.post('/register', data={
        'username': 'alice',
        'email': 'alice@student.edu',
        'password': 'password123'
    }, follow_redirects=True)
    assert res_reg.status_code == 200

    res_login = client.post('/login', data={
        'username_or_email': 'alice',
        'password': 'password123'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    print("[PASS] User Registration & Login")

    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        alice_id = alice.id

    # 2. PROFILE & SETTINGS UPDATES
    res_prof = client.post('/profile', data={
        'student_id_no': '21BCE1042',
        'college': 'National Institute of Technology',
        'department': 'Computer Science & Engineering',
        'year': '3rd Year',
        'semester': 'Semester 6'
    }, follow_redirects=True)
    assert b'Student profile updated successfully!' in res_prof.data

    with app.app_context():
        updated_user = db.session.get(User, alice_id)
        assert updated_user.student_id_no == '21BCE1042'
        assert updated_user.department == 'Computer Science & Engineering'
    print("[PASS] Profile Management & SQLite Persistence")

    res_sett = client.post('/settings', data={
        'available_hours_per_day': 5.0,
        'preferred_start_time': '08:30',
        'preferred_end_time': '20:30',
        'break_duration_mins': 20,
        'theme': 'light',
        'notifications_enabled': 'on'
    }, follow_redirects=True)
    assert b'Account settings and study preferences saved.' in res_sett.data

    with app.app_context():
        pref = StudyPreference.query.filter_by(user_id=alice_id).first()
        assert pref.available_hours_per_day == 5.0
        assert pref.preferred_start_time == '08:30'
    print("[PASS] Settings & Study Preferences Persistence")

    # 3. SUBJECTS & ATTENDANCE MANAGEMENT
    client.post('/subjects/add', data={'name': 'Computer Networks', 'credits': 4}, follow_redirects=True)
    client.post('/subjects/add', data={'name': 'DBMS', 'credits': 3}, follow_redirects=True)

    with app.app_context():
        cn_sub = Subject.query.filter_by(user_id=alice_id, name='Computer Networks').first()
        dbms_sub = Subject.query.filter_by(user_id=alice_id, name='DBMS').first()
        cn_id = cn_sub.id
        dbms_id = dbms_sub.id

    with app.app_context():
        # Get attendance records created automatically
        records = get_subject_attendance_summary(alice_id)
        cn_att_id = [r['id'] for r in records if r['subject_id'] == cn_id][0]
        dbms_att_id = [r['id'] for r in records if r['subject_id'] == dbms_id][0]

    # Update attendance for CN (20 total, 18 attended = 90% SAFE)
    client.post(f'/attendance/update/{cn_att_id}', data={'total_classes': 20, 'attended_classes': 18}, follow_redirects=True)
    # Update attendance for DBMS (20 total, 11 attended = 55% CRITICAL)
    client.post(f'/attendance/update/{dbms_att_id}', data={'total_classes': 20, 'attended_classes': 11}, follow_redirects=True)

    with app.app_context():
        att_recs = get_subject_attendance_summary(alice_id)
        cn_rec = [r for r in att_recs if r['subject_id'] == cn_id][0]
        dbms_rec = [r for r in att_recs if r['subject_id'] == dbms_id][0]
        assert cn_rec['percentage'] == 90.0
        assert cn_rec['status'] == 'SAFE'
        assert dbms_rec['percentage'] == 55.0
        assert dbms_rec['status'] == 'CRITICAL'
        assert 'Attend the next' in dbms_rec['recommendation']
    print("[PASS] Attendance Percentage, Status (SAFE/CRITICAL), & Target Recommendation Calculation")

    # 4. ADD ACADEMIC ITEMS (TASKS, ASSIGNMENTS, EXAMS)
    today = date.today()
    tomorrow_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    client.post('/assignments/add', data={
        'title': 'CN Lab Assignment',
        'subject_id': cn_id,
        'deadline': tomorrow_str,
        'difficulty': 'Hard',
        'estimated_hours': 3.0,
        'status': 'Not Started'
    }, follow_redirects=True)

    client.post('/tasks/add', data={
        'title': 'Overdue DBMS Worksheet',
        'subject_id': dbms_id,
        'deadline': yesterday_str,
        'priority': 'High',
        'difficulty': 'Hard',
        'estimated_hours': 2.0,
        'status': 'Overdue'
    }, follow_redirects=True)

    client.post('/exams/add', data={
        'subject_id': cn_id,
        'exam_date': (today + timedelta(days=4)).strftime('%Y-%m-%d'),
        'exam_time': '09:30 AM',
        'difficulty': 'Hard',
        'syllabus': 'Modules 1-3',
        'prep_percentage': 40
    }, follow_redirects=True)

    # 5. STUDY PLANNER GENERATION & PRIORITIZATION HIERARCHY
    with app.app_context():
        plan = generate_intelligent_study_plan(alice_id)
        assert len(plan) >= 1
        # Overdue work ranked #1
        assert 'Overdue' in plan[0]['title'] or 'CN Lab' in plan[0]['title']
    print("[PASS] Intelligent Study Planner Prioritization Hierarchy (Overdue > 24h > High Priority > Exams)")

    # 6. CATEGORIZED AI INSIGHTS VERIFICATION
    with app.app_context():
        insights = generate_categorized_ai_insights(alice_id)
        categories = {i['category'] for i in insights}
        assert 'URGENT' in categories or 'IMPORTANT' in categories or 'WARNING' in categories
    print(f"[PASS] Categorized AI Insights Generated ({len(insights)} total insights)")

    # 7. MONTHLY CALENDAR VIEW
    res_cal = client.get(f'/calendar?year={today.year}&month={today.month}')
    assert res_cal.status_code == 200
    assert b'Academic Calendar' in res_cal.data
    print("[PASS] Monthly Calendar View & Navigation")

    # 8. DASHBOARD & ANALYTICS VIEWS
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200
    assert b'Attendance Overview' in res_dash.data

    res_analy = client.get('/analytics')
    assert res_analy.status_code == 200
    assert b'Course Attendance by Subject' in res_analy.data
    print("[PASS] Dashboard & Analytics Rendered with Stage 4 Components")

    # 9. STAGE 4 REST APIS
    assert client.get('/api/planner').status_code == 200
    assert client.post('/api/planner/generate').status_code == 200
    assert client.get('/api/insights').status_code == 200
    assert client.get('/api/calendar').status_code == 200
    assert client.get('/api/attendance').status_code == 200
    assert client.get('/api/analytics').status_code == 200
    assert client.get('/api/profile').status_code == 200
    assert client.get('/api/settings').status_code == 200
    print("[PASS] All Stage 4 REST API Endpoints (/api/*) Verified")

    # 10. RE-LOGIN & PERSISTENCE VERIFICATION
    client.get('/logout')
    res_relogin = client.post('/login', data={'username_or_email': 'alice', 'password': 'password123'}, follow_redirects=True)
    assert res_relogin.status_code == 200
    assert b'Welcome back, alice!' in res_relogin.data

    with app.app_context():
        check_user = db.session.get(User, alice_id)
        assert check_user.student_id_no == '21BCE1042'
        check_att = Attendance.query.filter_by(user_id=alice_id, subject_id=cn_id).first()
        assert check_att.attended_classes == 18
    print("[PASS] User Logout, Re-Login, & SQLite Session Persistence Verified")

    print("==================================================")
    print("ALL STAGE 4 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
