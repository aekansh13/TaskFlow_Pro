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

## Prerequisites

- Python 3.11+
- MongoDB Atlas Account
- OpenRouter API Key
- Railway Account (for deployment)

## Local Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd taskflow-pro
```

### 2. Create and activate a virtual environment

```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate
# macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory (one level above `backend/`):

```bash
MONGO_URI=mongodb+srv://...
SECRET_KEY=...
JWT_SECRET_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
OPENROUTER_API_KEY=...
```

### 5. Start the App

```bash
python backend/run.py
```

## Deployment (Railway Unified Stack)

TaskFlow Pro is designed to run as a **Unified Stack** on Railway. This means the frontend and backend are hosted on the same domain, eliminating CORS issues and ensuring secure cookie handling.

1.  **Connect GitHub**: Point Railway to your repository.
2.  **Environment Variables**: Add all keys from your `.env`.
3.  **Procfile**: Railway uses the root `Procfile` to start Gunicorn.
4.  **Database**: Use **MongoDB Atlas** for persistent storage.

## Cloud Troubleshooting Wins

During the cloud migration, several production-only hurdles were cleared:
- **Unified Origin**: Moved from split Hosting (Vercel/Render) to Unified (Railway) to solve SameSite cookie restrictions and cross-origin auth issues.
- **Proxy Bypass**: Resolved a `TypeError: proxies` crash in the `openai` SDK on cloud servers by switching to raw `requests` for the OpenRouter API.
- **Protocol Harmony**: Configured specific Google OAuth Redirect URIs to match the production `https` environment.

## Credits & Libraries

- **Flask**: Web framework
- **Alpine.js**: Lightweight frontend reactivity
- **Chart.js**: Analytics visualization
- **MongoEngine**: Object-Document Mapper
- **Authlib**: Secure OAuth integration
