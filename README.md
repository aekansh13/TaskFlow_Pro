# TaskFlow Pro

> A full-stack task management web application built with Python, Flask, MongoDB, and Vanilla JS.

## Features

- User registration & login with JWT (httpOnly cookies — XSS safe)
- Google OAuth 2.0 login
- Full task CRUD with filtering, search, priorities, and tags
- Repeating tasks (daily, weekdays, weekly, custom days)
- Pomodoro focus timer with session logging
- AI-powered subtask suggestions (OpenRouter / GPT-4o-mini)
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
| AI         | OpenRouter API (gpt-4o-mini)                  |
| Infrastructure| Railway (Unified Hosting)                    |
| Frontend   | HTML5, CSS3, Vanilla JS, Alpine.js             |


## Credits & Libraries

- **Flask**: Web framework
- **Alpine.js**: Lightweight frontend reactivity
- **Chart.js**: Analytics visualization
- **MongoEngine**: Object-Document Mapper
- **Authlib**: Secure OAuth integration
