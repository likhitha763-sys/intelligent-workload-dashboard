from datetime import date, timedelta
from models import db, Subject, Task, Assignment, Exam, Attendance, StudyPreference

def seed_engineering_demo_data(user_id):
    """
    Seeds realistic engineering academic workload data for evaluation and project demonstration
    STRICTLY for the authenticated user without affecting other students.
    """
    today = date.today()

    # 1. Clean existing records for current user
    Task.query.filter_by(user_id=user_id).delete()
    Assignment.query.filter_by(user_id=user_id).delete()
    Exam.query.filter_by(user_id=user_id).delete()
    Attendance.query.filter_by(user_id=user_id).delete()
    Subject.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    # 2. Add Engineering Subjects
    cn = Subject(user_id=user_id, name='Computer Networks', code='CS501', semester='Semester 5', faculty_name='Dr. Andrew Tanenbaum', credits=4)
    dbms = Subject(user_id=user_id, name='Database Management Systems', code='CS502', semester='Semester 5', faculty_name='Dr. E.F. Codd', credits=3)
    os_sub = Subject(user_id=user_id, name='Operating Systems', code='CS503', semester='Semester 5', faculty_name='Dr. A. Silberschatz', credits=4)
    dsa = Subject(user_id=user_id, name='Data Structures & Algorithms', code='CS302', semester='Semester 3', faculty_name='Dr. Donald Knuth', credits=4)
    se = Subject(user_id=user_id, name='Software Engineering', code='CS504', semester='Semester 5', faculty_name='Dr. Ian Sommerville', credits=3)

    db.session.add_all([cn, dbms, os_sub, dsa, se])
    db.session.commit()

    # 3. Add Realistic Tasks
    t1 = Task(
        user_id=user_id, subject_id=cn.id, title='Read Chapter 4 - Transport Layer Protocols',
        description='Focus on TCP 3-way handshake and congestion control mechanisms.',
        deadline=today + timedelta(days=1), priority='High', difficulty='Hard', estimated_hours=3.0, status='Not Started'
    )
    t2 = Task(
        user_id=user_id, subject_id=dbms.id, title='Practice B+ Tree & Indexing Exercises',
        description='Solve query optimization problems from tutorial sheet 3.',
        deadline=today + timedelta(days=3), priority='Medium', difficulty='Medium', estimated_hours=2.0, status='In Progress'
    )
    t3 = Task(
        user_id=user_id, subject_id=os_sub.id, title='Implement Page Replacement Simulator',
        description='Code FIFO, LRU, and Optimal page replacement in Python.',
        deadline=today - timedelta(days=1), priority='High', difficulty='Hard', estimated_hours=4.0, status='Overdue'
    )
    t4 = Task(
        user_id=user_id, subject_id=dsa.id, title='Revise Graph Traversal (DFS/BFS)',
        description='Review adjacency list representation and topological sort.',
        deadline=today + timedelta(days=5), priority='Low', difficulty='Easy', estimated_hours=1.5, status='Not Started'
    )
    t5 = Task(
        user_id=user_id, subject_id=se.id, title='Draw System Architecture Sequence Diagram',
        description='UML class and sequence diagrams for project milestone 1.',
        deadline=today + timedelta(days=2), priority='Medium', difficulty='Medium', estimated_hours=2.5, status='Not Started'
    )
    t6 = Task(
        user_id=user_id, subject_id=cn.id, title='Complete Wireshark Packet Trace Lab',
        description='Analyze HTTP and TCP header packet captures.',
        deadline=today - timedelta(days=3), priority='Medium', difficulty='Medium', estimated_hours=2.0, status='Completed'
    )

    db.session.add_all([t1, t2, t3, t4, t5, t6])

    # 4. Add Realistic Assignments
    a1 = Assignment(
        user_id=user_id, subject_id=cn.id, title='Socket Programming Multi-Threaded Server Assignment',
        description='Implement concurrent TCP echo server with custom message protocol.',
        deadline=today + timedelta(days=1), difficulty='Hard', estimated_hours=4.5, status='Not Started'
    )
    a2 = Assignment(
        user_id=user_id, subject_id=dbms.id, title='SQL Schema Design & Normalization Lab Report',
        description='Normalize sample university database schema up to 3NF/BCNF.',
        deadline=today + timedelta(days=4), difficulty='Medium', estimated_hours=3.0, status='In Progress'
    )
    a3 = Assignment(
        user_id=user_id, subject_id=se.id, title='Agile User Stories & Sprint Backlog Report',
        description='Create product backlog and estimation points for term project.',
        deadline=today - timedelta(days=2), difficulty='Easy', estimated_hours=2.0, status='Submitted'
    )

    db.session.add_all([a1, a2, a3])

    # 5. Add Upcoming Exams
    e1 = Exam(
        user_id=user_id, subject_id=cn.id, exam_date=today + timedelta(days=4), exam_time='09:30 AM',
        difficulty='Hard', syllabus='Modules 1 to 4: OSI Model, IP Addressing, Subnetting, TCP/UDP', prep_percentage=35
    )
    e2 = Exam(
        user_id=user_id, subject_id=dbms.id, exam_date=today + timedelta(days=10), exam_time='02:00 PM',
        difficulty='Medium', syllabus='Relational Algebra, SQL, Transactions, Concurrency Control', prep_percentage=60
    )

    db.session.add_all([e1, e2])

    # 6. Add Course Attendance Records
    att1 = Attendance(user_id=user_id, subject_id=cn.id, total_classes=24, attended_classes=22)       # 91.7% SAFE
    att2 = Attendance(user_id=user_id, subject_id=dbms.id, total_classes=20, attended_classes=14)     # 70.0% WARNING
    att3 = Attendance(user_id=user_id, subject_id=os_sub.id, total_classes=22, attended_classes=12)   # 54.5% CRITICAL
    att4 = Attendance(user_id=user_id, subject_id=dsa.id, total_classes=25, attended_classes=20)      # 80.0% SAFE
    att5 = Attendance(user_id=user_id, subject_id=se.id, total_classes=18, attended_classes=15)       # 83.3% SAFE

    db.session.add_all([att1, att2, att3, att4, att5])

    # 7. Update Study Preferences
    pref = StudyPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = StudyPreference(user_id=user_id)
        db.session.add(pref)
    
    pref.available_hours_per_day = 5.0
    pref.preferred_start_time = '09:00'
    pref.preferred_end_time = '21:00'
    pref.break_duration_mins = 15

    db.session.commit()
    return True
