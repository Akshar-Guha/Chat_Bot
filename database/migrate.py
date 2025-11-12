"""
Database Migration Manager for EideticRAG
Handles schema migrations and versioning
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from connection import NeonDBConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db: NeonDBConnection, migrations_dir: Optional[Path] = None):
        """
        Initialize migration manager
        
        Args:
            db: Database connection instance
            migrations_dir: Directory containing migration scripts
        """
        self.db = db
        self.migrations_dir = migrations_dir or Path(__file__).parent / "schema"
        
        # Ensure migrations table exists
        self._init_migrations_table()
    
    def _init_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        query = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(500) NOT NULL,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                execution_time_ms NUMERIC(10,2),
                status VARCHAR(20) DEFAULT 'success'
            );
        """
        self.db.execute_query(query)
        logger.info("Schema migrations table initialized")
    
    def get_applied_migrations(self) -> List[Dict]:
        """
        Get list of applied migrations
        
        Returns:
            List of applied migrations
        """
        query = """
            SELECT version, name, executed_at, status
            FROM schema_migrations
            ORDER BY executed_at;
        """
        return self.db.execute_query(query, fetch=True) or []
    
    def get_pending_migrations(self) -> List[Path]:
        """
        Get list of pending migration files
        
        Returns:
            List of pending migration file paths
        """
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return []
        
        # Get all SQL files
        all_migrations = sorted(self.migrations_dir.glob("*.sql"))
        
        # Get applied migration versions
        applied = self.get_applied_migrations()
        applied_versions = {m['version'] for m in applied}
        
        # Filter pending migrations
        pending = [
            m for m in all_migrations
            if m.stem not in applied_versions
        ]
        
        return pending
    
    def apply_migration(self, migration_path: Path) -> bool:
        """
        Apply a single migration
        
        Args:
            migration_path: Path to migration file
        
        Returns:
            True if successful
        """
        version = migration_path.stem
        name = migration_path.name
        
        logger.info(f"Applying migration: {name}")
        
        start_time = datetime.now()
        
        try:
            # Execute migration script
            self.db.execute_script(migration_path)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record migration
            query = """
                INSERT INTO schema_migrations (version, name, execution_time_ms, status)
                VALUES (%s, %s, %s, 'success')
                ON CONFLICT (version) DO NOTHING;
            """
            self.db.execute_query(query, (version, name, execution_time))
            
            logger.info(f"Migration applied successfully: {name} ({execution_time:.2f}ms)")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {name} - {e}")
            
            # Record failed migration
            query = """
                INSERT INTO schema_migrations (version, name, status)
                VALUES (%s, %s, 'failed')
                ON CONFLICT (version) DO UPDATE SET status = 'failed';
            """
            self.db.execute_query(query, (version, name))
            
            raise
    
    def migrate(self) -> int:
        """
        Apply all pending migrations
        
        Returns:
            Number of migrations applied
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        logger.info(f"Found {len(pending)} pending migration(s)")
        
        applied_count = 0
        for migration_path in pending:
            try:
                self.apply_migration(migration_path)
                applied_count += 1
            except Exception as e:
                logger.error(f"Migration aborted due to error: {e}")
                break
        
        logger.info(f"Applied {applied_count} migration(s)")
        return applied_count
    
    def rollback(self, version: str):
        """
        Rollback a migration (placeholder - implement based on needs)
        
        Args:
            version: Migration version to rollback
        """
        logger.warning("Rollback not implemented - manual rollback required")
        # Implement rollback logic based on your needs
        # This typically requires separate rollback scripts
    
    def get_migration_status(self) -> Dict:
        """
        Get migration status summary
        
        Returns:
            Migration status information
        """
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'last_migration': applied[-1] if applied else None,
            'applied_migrations': applied,
            'pending_migrations': [m.name for m in pending]
        }


def main():
    """Main migration script"""
    try:
        # Initialize database connection
        logger.info("Connecting to Neon database...")
        db = NeonDBConnection()
        
        # Test connection
        if not db.test_connection():
            logger.error("Database connection failed")
            return
        
        logger.info("Database connection successful")
        
        # Initialize migration manager
        migration_manager = MigrationManager(db)
        
        # Show current status
        status = migration_manager.get_migration_status()
        logger.info(f"Migration status: {status['applied_count']} applied, {status['pending_count']} pending")
        
        # Apply migrations
        applied_count = migration_manager.migrate()
        
        if applied_count > 0:
            logger.info(f"✓ Successfully applied {applied_count} migration(s)")
        else:
            logger.info("✓ Database schema is up to date")
        
        # Show final status
        final_status = migration_manager.get_migration_status()
        if final_status['last_migration']:
            logger.info(f"Current schema version: {final_status['last_migration']['version']}")
        
        # Close connection
        db.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
