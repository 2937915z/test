# StudyHub (Learning Activity Management System)

A Django-based web application for university students / self-learners to manage:
- Courses and attendance records
- Assignments and deadlines
- Daily planning
- Focus sessions (Pomodoro-style)
- Dashboard statistics

This project was developed for coursework5 implementation using **Python + Django**, with **HTML/CSS (Bootstrap)** and **JavaScript (AJAX/Fetch)** for client-side interactivity.

---

## Features (Mapped to User Stories)

### Must-have (M1–M6)
- **M1 Authentication**
  - Register / Login / Logout (session-based authentication)
- **M2 Course Management**
  - Create and manage course entries
- **M3 Attendance Records**
  - Record attendance per course/date with status:
    - Present
    - Late
    - Absent
- **M4 Assignment Tracking**
  - Add assignments with due date and status
  - Update assignment status dynamically (AJAX)
- **M5 Daily Planning**
  - Add/import daily plan items
  - Mark plan items as done
- **M6 Focus Session Tracking**
  - Start/finish focus sessions and save records to the database

### Should-have (S1)
- **Dashboard / Statistics**
  - Weekly focus minutes
  - Upcoming assignments
  - Attendance rate

---

## Tech Stack

- **Backend**: Python, Django
- **Frontend**: Django Templates, Bootstrap, JavaScript (Fetch/AJAX)
- **Database (Development)**: SQLite
- **Testing**: Django TestCase

---

## Project Structure

```text
CW5/
├── manage.py
├── requirements.txt
├── README.md
├── core/
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── static/
│   ├── css/
│   │   └── app.css
│   └── js/
│       ├── assignments.js
│       ├── attendance.js
│       └── plan_focus.js
├── studyhub/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── registration/
    │   └── login.html
    ├── auth/
    │   └── register.html
    ├── courses/
    │   └── courses.html
    ├── assignments/
    │   └── assignments.html
    └── plan_focus/
        └── plan_focus.html

```
---
        
## Setup (Local Development)
  Run all commands in the project root directory (where manage.py is located).

Create and activate a virtual environment (Windows / PowerShell)
  ```Bash 
    python -m venv .venv
    .venv\Scripts\Activate.ps1
  ```

If PowerShell blocks execution, run:
  ```PowerShell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```

Then activate again:
  ```Bash
    .venv\Scripts\Activate.ps1
  ```


## Install Dependencies
  ```Bash
    pip install -r requirements.txt
  ```


## Database Migration
  ```Bash
    python manage.py makemigrations
    python manage.py migrate
  ```
Development database uses SQLite (db.sqlite3).


## Run the Project
  ```Bash
    python manage.py runserver
  ```
Open in browser:
  http://127.0.0.1:8000/
  http://127.0.0.1:8000/accounts/login/
  http://127.0.0.1:8000/accounts/register/


## Run Tests
  ```Bash
    python manage.py test
  ```
Current tests include examples for:
  Attendance unique constraint (one record per user/course/date)
  FocusSession XOR validation
  Login-required redirect
  Assignment status AJAX update endpoint


## Main Routes
  / → Dashboard
  /accounts/register/ → Register
  /accounts/login/ → Login
  /accounts/logout/ → Logout
  /courses/ → Courses + Attendance
  /assignments/ → Assignment Management
  /plan-focus/ → Daily Plan + Focus Session page

## Front-end Interactivity (AJAX Evidence)
  This project uses JavaScript Fetch/AJAX to update data without full page reload in several places:
  Attendance status updates (Present / Late / Absent)
  Assignment status updates
  Daily plan item toggle / import from assignments
  Focus session save

This satisfies the coursework requirement for client-side interactivity (not only static server rendering).


## Accessibility Notes (Implementation Highlights)
  Implemented / partially implemented accessibility-related improvements include:
  Form error text feedback (error identification)
  ARIA live status region for system messages (role="status", aria-live="polite")
  Hidden labels for attendance dropdowns (visually-hidden)
  Keyboard-accessible native form controls and buttons

Further accessibility evaluation evidence (screenshots/checks) is documented in the final report.


## Known Limitations / Current Iteration Scope
  Authentication currently uses Django default username login (email is stored and validated as unique during registration).

  Assignment status supports AJAX updates, but full edit flow / due-date AJAX update is not fully implemented in this iteration.

  FocusSession backend supports linking to Assignment or DailyPlanItem; current front-end UI may prioritise DailyPlanItem linking depending on the page version.

  M5 and M6 are implemented on a combined page (/plan-focus/) for workflow integration.
