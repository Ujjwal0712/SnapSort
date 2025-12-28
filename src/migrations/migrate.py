"""
Database Migration Runner
Run raw SQL migrations in order, tracking which have been applied.

Usage:
    python -m src.migrations.migrate
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.database import init_pool, get_db_connection, close_pool


MIGRATIONS_DIR = Path(__file__).parent

def get_applied_migrations(conn) -> set[str]:
    """Get list of already applied migration filenames"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM schema_migrations")
            return {row["filename"] for row in cur.fetchall()}
    except Exception:
        # Table doesn't exist yet, rollback and return empty set
        conn.rollback()
        return set()


def apply_migration(conn, filepath: Path) -> None:
    """Apply a single migration file"""
    sql = filepath.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        # Record that this migration was applied
        cur.execute(
            "INSERT INTO schema_migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING",
            (filepath.name,)
        )
    conn.commit()


def run_migrations() -> None:
    """Run all pending migrations in order"""
    print("🚀 Starting database migrations...")
    
    # Initialize connection pool
    init_pool()
    
    # Get all .sql files sorted by name
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found.")
        return
    
    with get_db_connection() as conn:
        applied = get_applied_migrations(conn)
        pending = [f for f in migration_files if f.name not in applied]
        
        if not pending:
            print("✅ All migrations already applied.")
            return
        
        print(f"Found {len(pending)} pending migration(s):\n")
        
        for filepath in pending:
            print(f"  📄 Applying {filepath.name}...")
            try:
                apply_migration(conn, filepath)
                print(f"     ✅ Done")
            except Exception as e:
                print(f"     ❌ Failed: {e}")
                conn.rollback()
                raise
        
        print(f"\n🎉 Successfully applied {len(pending)} migration(s)!")
    
    close_pool()


if __name__ == "__main__":
    run_migrations()
