"""
User document model for TaskFlow Pro.
Handles both local (password) and Google OAuth users.
"""
from datetime import datetime
import bcrypt
import mongoengine as me


class User(me.Document):
    name = me.StringField(required=True, max_length=100)
    email = me.EmailField(required=True, unique=True)
    password_hash = me.StringField(null=True)          # None for OAuth users
    avatar_url = me.URLField(null=True)
    oauth_provider = me.StringField(
        choices=['google', 'local'], default='local'
    )
    oauth_id = me.StringField(null=True)
    created_at = me.DateTimeField(default=datetime.utcnow)
    last_login = me.DateTimeField(null=True)
    is_active = me.BooleanField(default=True)

    meta = {
        'collection': 'users',
        'indexes': ['email'],
        'strict': False,
    }

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    def set_password(self, raw_password: str) -> None:
        """Hash and store the user's password using bcrypt."""
        self.password_hash = bcrypt.hashpw(
            raw_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, raw_password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            raw_password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a JSON-safe dictionary (never includes password_hash)."""
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'oauth_provider': self.oauth_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
        }
