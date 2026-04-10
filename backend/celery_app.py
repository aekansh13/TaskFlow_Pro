"""
celery_app.py — Celery factory for TaskFlow Pro.
Creates a Celery instance bound to the Flask app context so
MongoEngine queries work inside background tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    """Wrap a Celery instance so every task runs inside the Flask app context."""
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Nightly beat schedule — runs auto_create_repeat_tasks at 00:05 UTC
    celery.conf.beat_schedule = {
        'auto-repeat-tasks': {
            'task': 'app.jobs.repeat_tasks.auto_create_repeat_tasks',
            'schedule': crontab(hour=0, minute=5),
        },
    }
    celery.conf.timezone = 'UTC'

    return celery


# Bootstrap: create app + celery so `celery -A celery_app.celery` works
from app import create_app  # noqa: E402

flask_app = create_app(os.environ.get('FLASK_ENV', 'development'))
celery = make_celery(flask_app)

# Register the repeat task as a named Celery task
from app.jobs.repeat_tasks import auto_create_repeat_tasks as _fn  # noqa: E402
celery.task(name='app.jobs.repeat_tasks.auto_create_repeat_tasks')(_fn)
