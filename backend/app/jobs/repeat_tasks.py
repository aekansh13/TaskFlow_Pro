"""
repeat_tasks.py — Nightly Celery job for TaskFlow Pro.
Runs at 00:05 UTC every day.
Finds all completed tasks that have a repeat schedule and
auto-creates the next occurrence if one doesn't already exist.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Day-name → weekday index (Monday=0)
_DAY_MAP = {
    'mon': 0, 'tue': 1, 'wed': 2,
    'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6,
}


def _next_due_date(task) -> datetime | None:
    """Calculate the next due_date for a repeating task."""
    base = task.due_date or datetime.utcnow()

    if task.repeat == 'daily':
        return base + timedelta(days=1)

    if task.repeat == 'weekdays':
        next_date = base + timedelta(days=1)
        # Skip Saturday (5) and Sunday (6)
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        return next_date

    if task.repeat == 'weekly':
        return base + timedelta(weeks=1)

    if task.repeat == 'custom':
        if not task.repeat_days:
            return None
        target_weekdays = {_DAY_MAP[d] for d in task.repeat_days if d in _DAY_MAP}
        next_date = base + timedelta(days=1)
        # Look ahead up to 7 days
        for _ in range(7):
            if next_date.weekday() in target_weekdays:
                return next_date
            next_date += timedelta(days=1)
        return None

    return None


def auto_create_repeat_tasks():
    """
    Main Celery task — called nightly.
    Imported and registered by celery_app.py.
    """
    from app.models.task import Task

    now = datetime.utcnow()
    repeating = Task.objects(repeat__ne='none', status='done')
    created_count = 0

    for task in repeating:
        try:
            # Skip if past the repeat end date
            if task.repeat_end_date and task.repeat_end_date < now:
                continue

            next_due = _next_due_date(task)
            if next_due is None:
                continue

            # Skip if a pending child task already exists
            existing = Task.objects(
                parent_task_id=task.id,
                status__ne='done',
            ).first()
            if existing:
                continue

            new_task = Task(
                title=task.title,
                description=task.description,
                priority=task.priority,
                tags=task.tags,
                assigned_to=task.assigned_to,
                repeat=task.repeat,
                repeat_days=task.repeat_days,
                repeat_end_date=task.repeat_end_date,
                status='todo',
                due_date=next_due,
                parent_task_id=task,
                created_by=task.created_by,
                pomodoro_count=0,
            )
            new_task.save()
            created_count += 1

        except Exception as exc:  # noqa: BLE001
            logger.error('Failed to repeat task %s: %s', task.id, exc)

    logger.info('auto_create_repeat_tasks: created %d new tasks.', created_count)
    return created_count
