web: gunicorn --worker-class eventlet -w 1 --chdir backend run:app
worker: cd backend && celery -A celery_app.celery worker --loglevel=info
beat: cd backend && celery -A celery_app.celery beat --loglevel=info
