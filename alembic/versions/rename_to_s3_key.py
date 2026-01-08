"""rename_selfie_public_id_to_s3_key

Revision ID: rename_to_s3_key
Revises: create_user_sessions
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rename_to_s3_key'
down_revision: Union[str, Sequence[str], None] = 'create_user_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename selfie_public_id column to s3_key."""
    op.execute("""
        ALTER TABLE users 
        RENAME COLUMN selfie_public_id TO s3_key;
    """)


def downgrade() -> None:
    """Rename s3_key column back to selfie_public_id."""
    op.execute("""
        ALTER TABLE users 
        RENAME COLUMN s3_key TO selfie_public_id;
    """)
