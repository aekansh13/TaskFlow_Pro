# TaskFlow Pro

> A full-stack task management web application built with Python, Flask, MongoDB, and Vanilla JS.

## Features

- User registration & login with JWT (httpOnly cookies — XSS safe)
- Google OAuth 2.0 login
- Full task CRUD with filtering, search, priorities, and tags
- Repeating tasks (daily, weekdays, weekly, custom days)
- Pomodoro focus timer with session logging
- AI-powered subtask suggestions (OpenAI GPT-4o-mini)
- Analytics dashboard (completion rate, streak, charts)
- Calendar view with drag-and-drop rescheduling
- PDF export of task list
- Browser push notifications for due tasks
- Dark mode

## Tech Stack

| Layer      | Technology                                      |
|------------|------------------------------------------------|
| Backend    | Python 3.11, Flask, Flask-JWT-Extended, Flask-CORS, Flask-SocketIO |
| Database   | MongoDB (via MongoEngine)                      |
| Auth       | JWT in httpOnly cookies, Google OAuth (Authlib)|
| Jobs       | Celery + Redis                                 |
| AI         | OpenAI Python SDK (gpt-4o-mini)               |
| Frontend   | HTML5, CSS3, Vanilla JS, Alpine.js             |
| Charts     | Chart.js 4.x                                  |
| Calendar   | FullCalendar 6.x                               |
| Drag/Drop  | SortableJS 1.x                                 |
| Toasts     | Toastify-js 1.x                               |
| PDF        | jsPDF 2.x                                     |

## Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- Redis (local or cloud)


## Libraries Used

| Library              | Version | Purpose                          |
|----------------------|---------|----------------------------------|
| flask                | 3.0.3   | Web framework                    |
| flask-jwt-extended   | 4.6.0   | JWT auth with cookie support     |
| flask-cors           | 4.0.1   | Cross-Origin Resource Sharing    |
| flask-socketio       | 5.3.6   | WebSocket support                |
| mongoengine          | 0.28.2  | MongoDB ODM                      |
| bcrypt               | 4.1.3   | Password hashing                 |
| celery               | 5.3.6   | Background task queue            |
| marshmallow          | 3.21.3  | Input validation / serialisation |
| authlib              | 1.3.1   | Google OAuth 2.0                 |
| python-dotenv        | 1.0.1   | .env file loading                |
| gunicorn             | 22.0.0  | WSGI production server           |
| openai               | 1.30.1  | AI subtask suggestions           |
| redis                | 5.0.4   | Celery broker client             |
| eventlet             | 0.36.1  | Async mode for SocketIO          |
