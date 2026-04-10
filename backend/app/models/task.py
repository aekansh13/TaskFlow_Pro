"""
Task document model for TaskFlow Pro.
Includes subtask embedding, repeat scheduling, and Pomodoro tracking.
"""
from datetime import datetime
import mongoengine as me
from .user import User


class Subtask(me.EmbeddedDocument):
    text = me.StringField(required=True)
    done = me.BooleanField(default=False)

    def to_dict(self) -> dict:
        return {'text': self.text, 'done': self.done}


class Task(me.Document):
    # Core fields
    title = me.StringField(required=True, max_length=200)
    description = me.StringField(max_length=2000, default='')
    status = me.StringField(
        choices=['todo', 'in_progress', 'done'], default='todo'
    )
    priority = me.StringField(
        choices=['low', 'medium', 'high', 'critical'], default='medium'
    )
    tags = me.ListField(me.StringField())
    due_date = me.DateTimeField(null=True)

    # Ownership
    created_by = me.ReferenceField(User, required=True, reverse_delete_rule=me.CASCADE)
    assigned_to = me.ReferenceField(User, null=True, reverse_delete_rule=me.NULLIFY)

    # Subtasks
    subtasks = me.ListField(me.EmbeddedDocumentField(Subtask), default=list)

    # Timestamps
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    completed_at = me.DateTimeField(null=True)

    # Repeat fields
    repeat = me.StringField(
        choices=['none', 'daily', 'weekdays', 'weekly', 'custom'], default='none'
    )
    repeat_days = me.ListField(me.StringField())   # e.g. ['mon', 'wed', 'fri']
    repeat_end_date = me.DateTimeField(null=True)
    parent_task_id = me.ReferenceField('Task', null=True)

    # Pomodoro
    pomodoro_count = me.IntField(default=0)

    meta = {
        'collection': 'tasks',
        'indexes': ['created_by', 'status', 'priority', 'due_date', 'repeat'],
    }

    # ------------------------------------------------------------------
    # Save override — timestamps + completion tracking
    # ------------------------------------------------------------------

    def save(self, *args, **kwargs):
        now = datetime.utcnow()
        self.updated_at = now

        if self.status == 'done' and self.completed_at is None:
            self.completed_at = now
        elif self.status != 'done':
            self.completed_at = None

        return super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _ref_to_str(self, ref) -> str | None:
        """Safely convert a ReferenceField value to a string id."""
        if ref is None:
            return None
        # After fetch it's a Document; before fetch it's a DBRef
        try:
            return str(ref.id)
        except AttributeError:
            return str(ref)

    def to_dict(self) -> dict:
        """Return a fully JSON-serialisable dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'tags': self.tags,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_by': self._ref_to_str(self.created_by),
            'assigned_to': self._ref_to_str(self.assigned_to),
            'subtasks': [s.to_dict() for s in self.subtasks],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'repeat': self.repeat,
            'repeat_days': self.repeat_days,
            'repeat_end_date': self.repeat_end_date.isoformat() if self.repeat_end_date else None,
            'parent_task_id': self._ref_to_str(self.parent_task_id),
            'pomodoro_count': self.pomodoro_count,
        }
