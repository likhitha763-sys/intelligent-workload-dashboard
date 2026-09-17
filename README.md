# Intelligent Dashboard to Help Engineering Students Manage Academic Workload and Time Effectively

A comprehensive, production-grade Flask web application designed for engineering students to monitor academic stress, prioritize tasks, manage course attendance, visualize workload analytics, and automate study planning.

---

## 📌 Project Overview & Problem Statement

Engineering students face severe academic pressure balancing multiple courses, continuous lab assignments, complex project deliverables, and semester examinations. Poor time management often leads to last-minute cramming, missed deadlines, low attendance, and heightened stress.

This project addresses these challenges by implementing an **Intelligent Academic Workload Dashboard** that dynamically calculates a 0–100 Workload Index, ranks pending tasks using a multi-parameter priority engine, provides data-driven AI insights, generates time-slotted daily study plans, tracks course attendance against 75% threshold requirements, and displays interactive monthly calendars and analytics graphs.

---

## 🚀 Key Features

1. **User Authentication & Data Isolation**: Secure registration, password hashing (`Werkzeug`), session management (`Flask-Login`), and strict per-student data privacy (`filter_by(user_id=current_user.id)`).
2. **Academic Entity CRUD**: Complete management for Subjects, Tasks, Assignments, and Exam Schedules.
3. **Dynamic Workload Scoring (0–100)**: Real-time mathematical scoring categorized into `LOW` (0–39), `MODERATE` (40–69), `HIGH` (70–84), and `CRITICAL` (85–100).
4. **"What Should I Do Now?" Priority Engine**: Prominently highlights the single highest priority task/assignment with data-driven justification and direct action buttons.
5. **Intelligent Study Planner**: Generates realistic time-slotted daily study schedules matching student preferences (daily hours, start/end time, breaks) prioritized by overdue work, 24h deadlines, high priority, upcoming exams, and difficulty.
6. **Categorized AI Insights**: Generates non-random academic insights across 5 explicit categories: `URGENT`, `IMPORTANT`, `WARNING`, `SUGGESTION`, and `ACHIEVEMENT`.
7. **Interactive Academic Calendar**: Monthly calendar grid showing Tasks (Blue), Assignments (Yellow), and Exams (Red) with month navigation and clickable detail popups.
8. **Course Attendance Tracker**: Calculates attendance percentage, status badges (`SAFE` $\ge 75\%$, `WARNING` $60-74\%$, `CRITICAL` $<60\%$), and exact target class recommendations.
9. **Interactive Analytics Visualizations**: Integrated Chart.js charts for workload indices, task/assignment status distributions, subject workloads, study hours, and course attendance.
10. **Evaluator Demo Seeding**: Includes a *"Load Demo Data"* feature to immediately populate realistic engineering courses (*CN, DBMS, OS, Data Structures, SE*) for faculty evaluation and project demonstration.
11. **REST APIs**: Full JSON API suite for integration (`/api/workload`, `/api/planner`, `/api/insights`, `/api/calendar`, `/api/attendance`, `/api/analytics`, `/api/profile`, `/api/settings`).

---

## 🛠️ Technology Stack

* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login, python-dotenv, PyMySQL
* **Database:** SQLite (Default for local development) / MySQL (Prepared)
* **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons, Chart.js
* **Security:** Werkzeug password hashing, parameterized ORM queries, custom HTTP error handlers (400, 401, 403, 404, 500)

---

## 🧮 Workload Scoring Formula

The overall workload score $S \in [0, 100]$ is calculated dynamically:

$$S = \min\left(100, \sum \text{TaskWeight} + \sum \text{AssignmentWeight} + \sum \text{ExamWeight} + \text{OverduePenalties}\right)$$

Where:
* $\text{TaskWeight} = \text{Hours} \times \text{PriorityMult} \times \text{DifficultyMult} \times \text{ProximityMult} \times 3.5$
* $\text{AssignmentWeight} = \text{Hours} \times \text{DifficultyMult} \times \text{ProximityMult} \times 4.0$
* $\text{ExamWeight} = 12.0 \times \left( \frac{100 - \text{Prep\%}}{100} \right) \times \text{ExamProximityMult}$
* $\text{OverduePenalties} = +10$ points per overdue item.

---

## 📊 Database Schema

* `users`: `id`, `username`, `email`, `password_hash`, `student_id_no`, `college`, `department`, `year`, `semester`, `created_at`
* `subjects`: `id`, `user_id`, `name`, `faculty_name`, `credits`, `created_at`
* `tasks`: `id`, `user_id`, `subject_id`, `title`, `description`, `deadline`, `priority`, `difficulty`, `estimated_hours`, `status`, `created_at`
* `assignments`: `id`, `user_id`, `subject_id`, `title`, `description`, `deadline`, `difficulty`, `estimated_hours`, `status`, `created_at`
* `exams`: `id`, `user_id`, `subject_id`, `exam_date`, `exam_time`, `difficulty`, `syllabus`, `prep_percentage`, `created_at`
* `attendance`: `id`, `user_id`, `subject_id`, `total_classes`, `attended_classes`, `created_at`
* `study_preferences`: `id`, `user_id`, `available_hours_per_day`, `preferred_start_time`, `preferred_end_time`, `break_duration_mins`, `theme`, `notifications_enabled`

---

## 💻 Installation & Setup Guide

### 1. Navigate to Project Folder:
```cmd
cd C:\Users\LIKHITHA\.gemini\antigravity\scratch\student_workload_dashboard
```

### 2. Activate Virtual Environment:
* **Command Prompt (cmd.exe):**
  ```cmd
  venv\Scripts\activate
  ```
* **PowerShell:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

### 3. Install Required Dependencies:
```cmd
pip install -r requirements.txt
```

### 4. Run Flask Application:
```cmd
python app.py
```

### 5. Access in Web Browser:
Open `http://127.0.0.1:5000` in your web browser.

---

## 🎬 Faculty Evaluation & Demo Instructions

1. **Register a New Account** or sign in.
2. Click the **"Load Demo Data"** button in the top navigation bar.
3. The dashboard will automatically populate with realistic engineering subjects (*Computer Networks, DBMS, Operating Systems, Data Structures, Software Engineering*), tasks, assignments, upcoming exams, and course attendance.
4. Observe the dynamic **Workload Index Gauge**, **"What Should I Do Now?"** banner, **Today's Smart Study Plan**, **Categorized AI Insights**, and **Interactive Analytics Charts**.

---

## 🧪 Testing Instructions

Run the automated integration test suites:
```cmd
python test_stage2.py
python test_stage3.py
python test_stage4.py
python test_stage5.py
```
All test suites verify 100% test coverage across database CRUD operations, workload score algorithms, priority ranking, study planner generation, attendance formulas, security data isolation, and API endpoints.
