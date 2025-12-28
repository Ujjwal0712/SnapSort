"""create_users

Revision ID: 9d021915c7a7
Revises: 
Create Date: 2025-12-28 15:41:53.065789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d021915c7a7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users and related tables."""
    # Users table
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT FALSE,
            selfie_url TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # User credentials table
    op.execute("""
        CREATE TABLE user_credentials (
            user_id UUID PRIMARY KEY,
            password_hash VARCHAR NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_credentials_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)
    
    # User OTPs table
    op.execute("""
        CREATE TABLE user_otps (
            user_id UUID PRIMARY KEY,
            email_otp_hash VARCHAR,
            expires_at TIMESTAMPTZ NOT NULL,
            attempts SMALLINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_otps_user
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)
    
    # Indexes
    op.execute("CREATE INDEX idx_users_email ON users(email);")
    op.execute("CREATE INDEX idx_users_username ON users(username);")
    op.execute("CREATE INDEX idx_user_otps_user_id ON user_otps(user_id);")


def downgrade() -> None:
    """Drop all tables."""
    op.execute("DROP TABLE IF EXISTS user_otps;")
    op.execute("DROP TABLE IF EXISTS user_credentials;")
    op.execute("DROP TABLE IF EXISTS users;")
