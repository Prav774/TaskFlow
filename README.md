# TaskFlow – Intelligent Project & Task Management System

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-Framework-green)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-Frontend-06B6D4)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey)
![Status](https://img.shields.io/badge/Status-Completed-success)

## Overview

TaskFlow is a web-based Project and Task Management System developed using Django and Tailwind CSS. The platform helps organizations efficiently manage projects, assign tasks, monitor employee progress, and streamline project workflows.

The system provides separate interfaces for administrators and employees, enabling transparent project tracking, efficient collaboration, and improved productivity.

---

## Features

### Administrator Features

- Create and manage projects
- Break projects into multiple tasks
- Assign tasks to employees
- Reassign tasks when necessary
- Track task and project progress
- Review employee submissions
- Approve or reject completed work
- Monitor employee productivity
- Receive project status updates

### Employee Features

- Secure authentication system
- View assigned tasks
- Access task details and deadlines
- Update task progress
- Submit completed work
- Track project status
- Receive notifications and updates

### Notification System

- Task assignment alerts
- Status update notifications
- Deadline reminders
- Submission feedback notifications

---

## Technology Stack

### Backend
- Python
- Django

### Frontend
- HTML5
- CSS3
- Tailwind CSS
- JavaScript

### Database
- SQLite

### Tools
- Git
- GitHub
- VS Code

---

## Project Structure

```text
TaskFlow/
│
├── accounts/
├── notifications/
├── projects/
├── static/
├── templates/
├── taskflow/
│
├── manage.py
├── requirements.txt
├── package.json
├── package-lock.json
└── tailwind.config.js
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Prav774/TaskFlow.git
cd taskflow
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Apply Migrations

```bash
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Run Development Server

```bash
python manage.py runserver
```

Visit:

```text
http://127.0.0.1:8000/
```

---

## Workflow

### Admin Workflow

1. Create a Project
2. Create Tasks
3. Assign Tasks to Employees
4. Monitor Progress
5. Review Submissions
6. Approve Completion

### Employee Workflow

1. Login
2. View Assigned Tasks
3. Update Progress
4. Submit Work
5. Receive Feedback

---

## Security Features

- Django Authentication System
- Role-Based Access Control
- Session Management
- CSRF Protection
- Secure Password Hashing

---

## Future Enhancements

- Email Notifications
- REST API Integration
- Team Collaboration Features
- Advanced Analytics Dashboard
- Mobile Application
- AI-Based Task Prioritization

---

## Screenshots

### Login Page
<img width="1286" height="577" alt="image" src="https://github.com/user-attachments/assets/1c2289b7-bef2-4af0-8218-e246e32956f1" />


### Admin Dashboard
<img width="1302" height="625" alt="image" src="https://github.com/user-attachments/assets/ad334bd5-f7bc-4554-a146-096a07b3a432" />


### Employee Dashboard
<img width="1320" height="569" alt="image" src="https://github.com/user-attachments/assets/2e1e663f-baf0-4a81-962e-c9232025b666" />


### Project Management
<img width="1046" height="615" alt="image" src="https://github.com/user-attachments/assets/827dfb2d-bfb5-480c-bef8-5284d2b5a781" />


### Task Assignment
<img width="1021" height="637" alt="image" src="https://github.com/user-attachments/assets/197f54ae-5d81-47cd-8f52-83a808056fec" />


### Notifications
<img width="1051" height="562" alt="image" src="https://github.com/user-attachments/assets/28a462d8-96cd-414c-a730-3c0ff5300a11" />


---

## Learning Outcomes

This project helped strengthen skills in:

- Full Stack Web Development
- Django Framework
- Database Design
- Authentication & Authorization
- Project Workflow Management
- Tailwind CSS
- Git & GitHub

---

## Author

**Praveen V**

B.E CSE (CYBER SECURITY)

Karpagam College of Engineering

---

## License

This project is intended for educational, learning, and portfolio purposes.
