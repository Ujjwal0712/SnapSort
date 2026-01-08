"""add_selfie_public_id

Revision ID: add_selfie_public_id
Revises: 9d021915c7a7
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_selfie_public_id'
down_revision: Union[str, Sequence[str], None] = '9d021915c7a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add selfie_public_id column to users table."""
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN selfie_public_id VARCHAR(255);
    """)


def downgrade() -> None:
    """Remove selfie_public_id column."""
    op.execute("""
        ALTER TABLE users 
        DROP COLUMN IF EXISTS selfie_public_id;
    """)
