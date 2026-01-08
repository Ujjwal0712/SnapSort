"""create_user_sessions

Revision ID: create_user_sessions
Revises: add_selfie_public_id
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'create_user_sessions'
down_revision: Union[str, Sequence[str], None] = 'add_selfie_public_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_sessions table for refresh token management."""
    op.execute("""
        CREATE TABLE user_sessions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            refresh_token_hash VARCHAR UNIQUE NOT NULL,
            device_info VARCHAR,
            ip_address INET,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT fk_sessions_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)
    
    # Index for faster user session lookups
    op.execute("CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);")
    op.execute("CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);")


def downgrade() -> None:
    """Drop user_sessions table."""
    op.execute("DROP TABLE IF EXISTS user_sessions;")
