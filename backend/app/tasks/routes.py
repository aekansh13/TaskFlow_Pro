"""
Task routes for TaskFlow Pro.
Covers: CRUD, filtering, toggle complete, pomodoro logging,
        analytics, AI subtask suggestions.
All routes require JWT authentication via httpOnly cookies.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.models.task import Task
from app.models.user import User
from . import tasks_bp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user(user_id: str):
    try:
        return User.objects(id=user_id).first()
    except (InvalidId, Exception):
        return None


def _get_task_or_abort(task_id: str):
    """Return (task, error_response) tuple. One side is always None."""
    try:
        task = Task.objects(id=ObjectId(task_id)).first()
    except (InvalidId, Exception):
        return None, (jsonify({'error': 'Invalid task ID.'}), 400)
    if not task:
        return None, (jsonify({'error': 'Task not found.'}), 404)
    return task, None


# ---------------------------------------------------------------------------
# Marshmallow schema
# ---------------------------------------------------------------------------

class TaskSchema(Schema):
    title       = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(validate=validate.Length(max=2000), load_default='')
    status      = fields.Str(validate=validate.OneOf(['todo', 'in_progress', 'done']))
    priority    = fields.Str(validate=validate.OneOf(['low', 'medium', 'high', 'critical']))
    tags        = fields.List(fields.Str(validate=validate.Length(max=30)))
    due_date    = fields.DateTime(load_default=None)
    assigned_to = fields.Str(load_default=None)
    repeat      = fields.Str(validate=validate.OneOf(['none', 'daily', 'weekdays', 'weekly', 'custom']))
    repeat_days = fields.List(fields.Str())
    repeat_end_date = fields.DateTime(load_default=None)
    subtasks    = fields.List(fields.Dict(), load_default=None)

    @validates_schema
    def validate_assigned_to(self, data, **kwargs):
        uid = data.get('assigned_to')
        if uid and not User.objects(id=uid).first():
            from marshmallow import ValidationError as ME
            raise ME({'assigned_to': ['User not found.']})


_task_schema = TaskSchema()


# ---------------------------------------------------------------------------
# CRUD endpoints (Prompt 7)
# ---------------------------------------------------------------------------

@tasks_bp.get('')
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    user = _get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    # Base query — tasks the user owns OR is assigned to
    query = Task.objects.filter(
        __raw__={'$or': [{'created_by': user.id}, {'assigned_to': user.id}]}
    )

    # Optional filters
    status   = request.args.get('status')
    priority = request.args.get('priority')
    tag      = request.args.get('tag')
    search   = request.args.get('search')
    due_before = request.args.get('due_before')
    due_after  = request.args.get('due_after')

    if status:
        query = query.filter(status=status)
    if priority:
        query = query.filter(priority=priority)
    if tag:
        query = query.filter(tags=tag)
    if search:
        query = query.filter(title__icontains=search)
    if due_before:
        query = query.filter(due_date__lte=datetime.fromisoformat(due_before))
    if due_after:
        query = query.filter(due_date__gte=datetime.fromisoformat(due_after))

    tasks = query.order_by('-created_at')
    return jsonify([t.to_dict() for t in tasks])


@tasks_bp.post('')
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    user = _get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    json_data = request.get_json(silent=True) or {}
    errors = _task_schema.validate(json_data)
    if errors:
        return jsonify({'errors': errors}), 422

    data = _task_schema.load(json_data)
    if not data.get('title'):
        return jsonify({'errors': {'title': ['Title is required.']}}), 422

    task = Task(created_by=user)

    _apply_task_data(task, data)
    task.save()
    return jsonify(task.to_dict()), 201


@tasks_bp.get('/<task_id>')
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    task, err = _get_task_or_abort(task_id)
    if err:
        return err

    creator_id  = str(task.created_by.id) if task.created_by else None
    assigned_id = str(task.assigned_to.id) if task.assigned_to else None

    if user_id not in (creator_id, assigned_id):
        return jsonify({'error': 'Not authorised.'}), 403

    return jsonify(task.to_dict())


@tasks_bp.put('/<task_id>')
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    task, err = _get_task_or_abort(task_id)
    if err:
        return err

    if str(task.created_by.id) != user_id:
        return jsonify({'error': 'Only the task creator can edit this task.'}), 403

    json_data = request.get_json(silent=True) or {}
    errors = _task_schema.validate(json_data, partial=True)
    if errors:
        return jsonify({'errors': errors}), 422

    data = _task_schema.load(json_data, partial=True)
    _apply_task_data(task, data)
    task.save()
    return jsonify(task.to_dict())


@tasks_bp.delete('/<task_id>')
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task, err = _get_task_or_abort(task_id)
    if err:
        return err

    if str(task.created_by.id) != user_id:
        return jsonify({'error': 'Only the task creator can delete this task.'}), 403

    task.delete()
    return jsonify({'message': 'Task deleted'})


@tasks_bp.patch('/<task_id>/complete')
@jwt_required()
def toggle_complete(task_id):
    user_id = get_jwt_identity()
    task, err = _get_task_or_abort(task_id)
    if err:
        return err

    creator_id  = str(task.created_by.id) if task.created_by else None
    assigned_id = str(task.assigned_to.id) if task.assigned_to else None
    if user_id not in (creator_id, assigned_id):
        return jsonify({'error': 'Not authorised.'}), 403

    task.status = 'todo' if task.status == 'done' else 'done'
    task.save()
    return jsonify(task.to_dict())


@tasks_bp.patch('/<task_id>/pomodoro')
@jwt_required()
def log_pomodoro(task_id):
    user_id = get_jwt_identity()
    task, err = _get_task_or_abort(task_id)
    if err:
        return err

    creator_id  = str(task.created_by.id) if task.created_by else None
    assigned_id = str(task.assigned_to.id) if task.assigned_to else None
    if user_id not in (creator_id, assigned_id):
        return jsonify({'error': 'Not authorised.'}), 403

    task.pomodoro_count = (task.pomodoro_count or 0) + 1
    task.save()
    return jsonify(task.to_dict())


# ---------------------------------------------------------------------------
# Analytics endpoint (Prompt 8)
# ---------------------------------------------------------------------------

@tasks_bp.get('/analytics')
@jwt_required()
def analytics():
    user_id = get_jwt_identity()
    user = _get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    all_tasks = list(Task.objects(created_by=user))
    now = datetime.utcnow()
    today = now.date()

    total_tasks = len(all_tasks)
    done_tasks  = [t for t in all_tasks if t.status == 'done']

    completed_today = sum(
        1 for t in done_tasks
        if t.completed_at and t.completed_at.date() == today
    )

    completion_rate = round(len(done_tasks) / total_tasks * 100, 1) if total_tasks else 0.0

    overdue_count = sum(
        1 for t in all_tasks
        if t.due_date and t.due_date < now and t.status != 'done'
    )

    by_status = {
        'todo':        sum(1 for t in all_tasks if t.status == 'todo'),
        'in_progress': sum(1 for t in all_tasks if t.status == 'in_progress'),
        'done':        len(done_tasks),
    }

    by_priority = {
        p: sum(1 for t in all_tasks if t.priority == p)
        for p in ['low', 'medium', 'high', 'critical']
    }

    # Daily completions — last 14 days
    dates_14 = [(today - timedelta(days=i)) for i in range(13, -1, -1)]
    completion_map = Counter(
        t.completed_at.date()
        for t in done_tasks
        if t.completed_at and t.completed_at.date() in dates_14
    )
    daily_completions = [
        {'date': str(d), 'count': completion_map.get(d, 0)}
        for d in dates_14
    ]

    # Top 5 tags
    tag_counter: Counter = Counter()
    for t in all_tasks:
        tag_counter.update(t.tags or [])
    top_tags = [
        {'tag': tag, 'count': count}
        for tag, count in tag_counter.most_common(5)
    ]

    # Streak — consecutive days ending today with ≥1 completion
    completion_days = {
        t.completed_at.date()
        for t in done_tasks
        if t.completed_at
    }
    streak = 0
    check_day = today
    while check_day in completion_days:
        streak += 1
        check_day -= timedelta(days=1)

    return jsonify({
        'total_tasks':        total_tasks,
        'completed_today':    completed_today,
        'completion_rate':    completion_rate,
        'overdue_count':      overdue_count,
        'by_status':          by_status,
        'by_priority':        by_priority,
        'daily_completions':  daily_completions,
        'top_tags':           top_tags,
        'streak':             streak,
    })


# ---------------------------------------------------------------------------
# AI subtask suggestion endpoint (Prompt 9)
# ---------------------------------------------------------------------------

@tasks_bp.post('/suggest')
@jwt_required()
def suggest_subtasks():
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()

    if not title or not (3 <= len(title) <= 200):
        return jsonify({'error': 'title must be between 3 and 200 characters.'}), 400

    _FALLBACK = {
        'subtasks': ['Break down the task', 'Research requirements', 'Draft a plan', 'Review and finalize'],
        'fallback': True,
    }

    try:
        from openai import OpenAI, DefaultHttpxClient
        import os
        
        # Configure for OpenRouter
        # We explicitly set proxies=None to fix the 'unexpected keyword argument proxies' error on cloud servers.
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            http_client=DefaultHttpxClient(proxies=None)
        )

        prompt = (
            f"You are a productivity assistant. A user has a task titled: '{title}'. "
            "Generate exactly 4 specific, actionable subtasks to complete this task. "
            "Each subtask should be a concrete action starting with a verb. "
            "Respond ONLY with a valid JSON array of 4 strings. No explanation, no markdown."
        )

        completion = client.chat.completions.create(
            model='openai/gpt-4o-mini', # Provider-prefixed for OpenRouter
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=300,
            temperature=0.7,
            extra_headers={
                "HTTP-Referer": "https://taskflow-pro.local", # Optional
                "X-Title": "TaskFlow Pro",
            }
        )

        raw = completion.choices[0].message.content.strip()
        # Strip accidental markdown code fences
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]

        import json
        subtasks = json.loads(raw)
        if not isinstance(subtasks, list) or len(subtasks) != 4:
            return jsonify(_FALLBACK)

        return jsonify({'subtasks': subtasks})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(_FALLBACK)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _apply_task_data(task: Task, data: dict):
    """Apply validated schema data onto a Task document."""
    simple_fields = [
        'title', 'description', 'status', 'priority',
        'tags', 'due_date', 'repeat', 'repeat_days', 'repeat_end_date',
    ]
    for field in simple_fields:
        if field in data and data[field] is not None:
            setattr(task, field, data[field])

    if 'assigned_to' in data and data['assigned_to']:
        assigned = User.objects(id=data['assigned_to']).first()
        if assigned:
            task.assigned_to = assigned

    if 'subtasks' in data and data['subtasks'] is not None:
        from app.models.task import Subtask
        task.subtasks = [
            Subtask(text=s.get('text', ''), done=s.get('done', False))
            for s in data['subtasks']
            if s.get('text')
        ]
