import unittest
from datetime import date, timedelta
from app import app
from models.models import db, User, Subject, Task, Assignment, Exam, Attendance, StudyPreference
from services.workload_service import calculate_overall_workload
from services.planner_service import generate_intelligent_study_plan
from services.ai_insights_service import generate_categorized_ai_insights

from config import TestConfig

class Stage6TestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.from_object(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Clean database records for test isolation
        db.session.query(Task).delete()
        db.session.query(Assignment).delete()
        db.session.query(Exam).delete()
        db.session.query(Attendance).delete()
        db.session.query(Subject).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Create two isolated test users
        self.user1 = User(username="Student1", email="student1@edu.com")
        self.user1.set_password("Pass123!")
        self.user2 = User(username="Student2", email="student2@edu.com")
        self.user2.set_password("Pass123!")

        db.session.add_all([self.user1, self.user2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def login_user(self, username, password="Pass123!"):
        return self.client.post('/login', data={
            'username_or_email': username,
            'password': password
        }, follow_redirects=True)

    def test_subject_crud_with_code_and_semester(self):
        self.login_user("Student1")

        # 1. Add Subject with Code and Semester
        res = self.client.post('/subjects/add', data={
            'name': 'Cloud Computing',
            'code': 'CS601',
            'semester': 'Semester 6',
            'faculty_name': 'Dr. AWS',
            'credits': 4
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        sub = Subject.query.filter_by(user_id=self.user1.id, name='Cloud Computing').first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.code, 'CS601')
        self.assertEqual(sub.semester, 'Semester 6')
        self.assertEqual(sub.credits, 4)

        # 2. Edit Subject
        res_edit = self.client.post(f'/subjects/{sub.id}/edit', data={
            'name': 'Advanced Cloud Computing',
            'code': 'CS601-ADV',
            'semester': 'Semester 6',
            'faculty_name': 'Dr. AWS Senior',
            'credits': 4
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)

        sub_updated = db.session.get(Subject, sub.id)
        self.assertEqual(sub_updated.name, 'Advanced Cloud Computing')
        self.assertEqual(sub_updated.code, 'CS601-ADV')

        # 3. Invalid Credits Validation (< 1)
        res_inv = self.client.post(f'/subjects/{sub.id}/edit', data={
            'name': 'Advanced Cloud Computing',
            'credits': 0
        }, follow_redirects=True)
        self.assertIn(b'Credits must be an integer between 1 and 10.', res_inv.data)

    def test_input_validations_and_negative_hours(self):
        self.login_user("Student1")

        # 1. Negative estimated hours task validation
        res_task = self.client.post('/tasks/add', data={
            'title': 'Bad Task',
            'estimated_hours': -2.5
        }, follow_redirects=True)
        self.assertIn(b'Estimated completion hours must be a positive number', res_task.data)

        # 2. Negative estimated hours assignment validation
        res_assign = self.client.post('/assignments/add', data={
            'title': 'Bad Assignment',
            'estimated_hours': 0
        }, follow_redirects=True)
        self.assertIn(b'Estimated completion hours must be a positive number', res_assign.data)

    def test_multi_user_data_isolation(self):
        # Create subject and task for User 1
        sub1 = Subject(user_id=self.user1.id, name="User1 Subject", code="U101")
        db.session.add(sub1)
        db.session.commit()

        task1 = Task(user_id=self.user1.id, subject_id=sub1.id, title="User1 Task")
        db.session.add(task1)
        db.session.commit()

        # Login as User 2
        self.login_user("Student2")

        # User 2 listing subjects should not see User1 Subject
        res_sub = self.client.get('/subjects')
        self.assertNotIn(b"User1 Subject", res_sub.data)

        # User 2 attempting to edit User 1's task should get 404
        res_edit = self.client.post(f'/tasks/{task1.id}/edit', data={'title': 'Hacked Task'})
        self.assertEqual(res_edit.status_code, 404)

    def test_workload_level_and_ai_insights(self):
        self.login_user("Student1")
        today = date.today()

        # Add heavy academic load to drive workload score to HIGH
        sub = Subject(user_id=self.user1.id, name="Operating Systems", code="CS503")
        db.session.add(sub)
        db.session.commit()

        t1 = Task(user_id=self.user1.id, subject_id=sub.id, title="Kernel Lab", deadline=today + timedelta(days=1), priority="High", difficulty="Hard", estimated_hours=4.0)
        a1 = Assignment(user_id=self.user1.id, subject_id=sub.id, title="Process Scheduler", deadline=today + timedelta(days=1), difficulty="Hard", estimated_hours=5.0)
        e1 = Exam(user_id=self.user1.id, subject_id=sub.id, exam_date=today + timedelta(days=2), difficulty="Hard", prep_percentage=20)
        db.session.add_all([t1, a1, e1])
        db.session.commit()

        workload = calculate_overall_workload(self.user1.id)
        self.assertGreaterEqual(workload['score'], 70)
        self.assertIn(workload['category'], ['HIGH', 'CRITICAL'])

        # Verify AI Insights generates data-bound suggestions
        insights = generate_categorized_ai_insights(self.user1.id)
        self.assertTrue(len(insights) > 0)
        self.assertTrue(any('Operating Systems' in i['text'] or 'Kernel Lab' in i['text'] or 'Process Scheduler' in i['text'] for i in insights))

    def test_demo_data_seeding_route(self):
        self.login_user("Student1")
        res = self.client.post('/demo-data/seed', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Engineering Demo Data loaded successfully", res.data)

        # Check DB records created
        subjects = Subject.query.filter_by(user_id=self.user1.id).all()
        self.assertEqual(len(subjects), 5)
        codes = [s.code for s in subjects if s.code]
        self.assertIn('CS501', codes)

if __name__ == '__main__':
    unittest.main()
