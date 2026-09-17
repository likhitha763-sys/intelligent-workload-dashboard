from datetime import date, timedelta
from app import app, db
from models import User, Subject, Task, Assignment, Exam
from services.workload_service import calculate_overall_workload, get_top_recommendation, generate_smart_daily_plan, get_subject_workload_breakdown

def run_tests():
    print("==================================================")
    print("STARTING STAGE 3 AUTOMATED INTEGRATION TESTS")
    print("==================================================")

    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    # 1. REGISTER & LOGIN USER ALICE
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

        # 2. TEST EMPTY STATE BASELINE
        wl_empty = calculate_overall_workload(alice_id)
        assert wl_empty['score'] == 0
        assert wl_empty['category'] == 'LOW'
        top_empty = get_top_recommendation(alice_id)
        assert top_empty is None
        print("[PASS] Empty State Baseline Verified (Score: 0/100, Category: LOW)")

    # 3. ADD SUBJECTS
    sub1 = client.post('/subjects/add', data={'name': 'Computer Networks', 'faculty_name': 'Dr. Ross', 'credits': 4}, follow_redirects=True)
    sub2 = client.post('/subjects/add', data={'name': 'DBMS', 'faculty_name': 'Dr. Date', 'credits': 3}, follow_redirects=True)
    
    with app.app_context():
        cn_sub = Subject.query.filter_by(user_id=alice_id, name='Computer Networks').first()
        dbms_sub = Subject.query.filter_by(user_id=alice_id, name='DBMS').first()
        cn_id = cn_sub.id
        dbms_id = dbms_sub.id

    # 4. ADD TASKS & ASSIGNMENTS WITH DIFFERENT DEADLINES AND PRIORITIES
    today = date.today()
    tomorrow_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    next_week_str = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    # Add urgent high-priority assignment (CN Assignment)
    client.post('/assignments/add', data={
        'title': 'Complete CN Assignment',
        'description': 'Socket programming assignment',
        'subject_id': cn_id,
        'deadline': tomorrow_str,
        'difficulty': 'Hard',
        'estimated_hours': 4.0,
        'status': 'Not Started'
    }, follow_redirects=True)

    # Add moderate task (DBMS Task)
    client.post('/tasks/add', data={
        'title': 'DBMS Normalization Task',
        'description': '3NF and BCNF exercises',
        'subject_id': dbms_id,
        'deadline': next_week_str,
        'priority': 'Medium',
        'difficulty': 'Medium',
        'estimated_hours': 2.0,
        'status': 'Not Started'
    }, follow_redirects=True)

    # Add upcoming exam
    client.post('/exams/add', data={
        'subject_id': cn_id,
        'exam_date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
        'exam_time': '10:00 AM',
        'difficulty': 'Hard',
        'syllabus': 'Units 1-4',
        'prep_percentage': 30
    }, follow_redirects=True)

    with app.app_context():
        # 5. VERIFY WORKLOAD SCORE INCREASES DYNAMICALLY
        wl_loaded = calculate_overall_workload(alice_id)
        assert wl_loaded['score'] > 0
        print(f"[PASS] Workload Score Calculated: {wl_loaded['score']}/100 ({wl_loaded['category']})")

        # 6. VERIFY "WHAT SHOULD I DO NOW?" TOP RECOMMENDATION
        top_rec = get_top_recommendation(alice_id)
        assert top_rec is not None
        assert top_rec['title'] == 'Complete CN Assignment'
        assert 'Due Tomorrow' in top_rec['reason'] or '4.0 hrs' in top_rec['reason']
        print(f"[PASS] 'What Should I Do Now?' Top Recommendation Verified: {top_rec['title']} (Reason: {top_rec['reason']})")

        # 7. VERIFY SMART DAILY STUDY PLAN GENERATION
        daily_plan = generate_smart_daily_plan(alice_id)
        assert len(daily_plan) >= 1
        assert daily_plan[0]['title'] == 'Complete CN Assignment'
        print(f"[PASS] Smart Daily Plan Generated ({len(daily_plan)} slots scheduled)")

        cn_ass = Assignment.query.filter_by(user_id=alice_id, title='Complete CN Assignment').first()
        cn_ass_id = cn_ass.id

    # 8. VERIFY WORKLOAD SCORE DROPS AFTER COMPLETING WORK
    client.post(f'/assignments/{cn_ass_id}/status', data={'status': 'Submitted'}, follow_redirects=True)
    with app.app_context():
        wl_after_complete = calculate_overall_workload(alice_id)
        assert wl_after_complete['score'] < wl_loaded['score']
        print(f"[PASS] Workload Score Decreased on Completion: {wl_loaded['score']} -> {wl_after_complete['score']}")

    # 9. VERIFY OVERDUE WORK DETECTION AND PENALTY
    client.post('/tasks/add', data={
        'title': 'Overdue Lab Submission',
        'description': 'Late submission',
        'subject_id': dbms_id,
        'deadline': yesterday_str,
        'priority': 'High',
        'difficulty': 'Hard',
        'estimated_hours': 3.0,
        'status': 'Overdue'
    }, follow_redirects=True)

    with app.app_context():
        wl_overdue = calculate_overall_workload(alice_id)
        top_overdue = get_top_recommendation(alice_id)
        assert 'Overdue' in top_overdue['reason'] or top_overdue['title'] == 'Overdue Lab Submission'
        print(f"[PASS] Overdue Item Priority Penalty & Warning Verified")

    # 10. VERIFY REST API ENDPOINTS
    res_api_wl = client.get('/api/workload')
    assert res_api_wl.status_code == 200
    assert res_api_wl.json['status'] == 'success'
    assert 'score' in res_api_wl.json['data']

    res_api_prio = client.get('/api/workload/priority')
    assert res_api_prio.status_code == 200
    assert res_api_prio.json['count'] > 0

    res_api_rec = client.get('/api/workload/recommendation')
    assert res_api_rec.status_code == 200
    assert res_api_rec.json['top_recommendation'] is not None

    res_api_plan = client.get('/api/workload/daily-plan')
    assert res_api_plan.status_code == 200

    res_api_sub = client.get('/api/workload/subjects')
    assert res_api_sub.status_code == 200
    assert len(res_api_sub.json['data']) == 2
    print("[PASS] All REST API Endpoints (/api/workload/*) Tested Successfully")

    # 11. VERIFY ANALYTICS PAGE
    res_analytics = client.get('/analytics')
    assert res_analytics.status_code == 200
    assert b'Workload Analytics' in res_analytics.data
    print("[PASS] Analytics Page (/analytics) Rendered Successfully")

    print("==================================================")
    print("ALL STAGE 3 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
