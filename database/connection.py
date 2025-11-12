"""
Database Connection Manager for Neon PostgreSQL
Handles connection pooling and database operations
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NeonDBConnection:
    """Neon PostgreSQL Database Connection Manager"""
    
    def __init__(
        self,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """
        Initialize database connection pool
        
        Args:
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool
        """
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            # Construct from individual components
            host = os.getenv('NEON_DB_HOST')
            database = os.getenv('NEON_DB_NAME', 'neondb')
            user = os.getenv('NEON_DB_USER')
            password = os.getenv('NEON_DB_PASSWORD')
            port = os.getenv('NEON_DB_PORT', '5432')
            sslmode = os.getenv('NEON_DB_SSLMODE', 'require')
            
            if not all([host, user, password]):
                raise ValueError("Database credentials not found in environment variables")
            
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
        
        # Create connection pool
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                self.database_url
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool (context manager)
        
        Yields:
            Database connection
        """
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Get a cursor from the pool (context manager)
        
        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)
        
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = False,
        fetch_one: bool = False,
        return_dict: bool = True
    ) -> Optional[Any]:
        """
        Execute a query
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            fetch_one: Whether to fetch only one result
            return_dict: Return results as dictionaries
        
        Returns:
            Query results or None
        """
        cursor_factory = extras.RealDictCursor if return_dict else None
        
        with self.get_cursor(cursor_factory=cursor_factory) as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch:
                return cursor.fetchall()
            
            return None
    
    def execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> int:
        """
        Execute query with multiple parameter sets
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        
        Returns:
            Number of rows affected
        """
        with self.get_cursor() as cursor:
            extras.execute_batch(cursor, query, params_list)
            return cursor.rowcount
    
    def execute_script(self, script_path: Path) -> bool:
        """
        Execute SQL script from file
        
        Args:
            script_path: Path to SQL script file
        
        Returns:
            True if successful
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script = f.read()
            
            with self.get_connection() as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cursor:
                    cursor.execute(script)
            
            logger.info(f"Script executed successfully: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute script {script_path}: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table
        
        Returns:
            True if table exists
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result['exists'] if result else False
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Number of rows
        """
        query = f"SELECT COUNT(*) as count FROM {table_name};"
        result = self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """
        Get column information for a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            List of column information
        """
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,), fetch=True)
    
    def close(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection is successful
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                logger.info("Database connection test successful")
                return result is not None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Singleton instance
_db_connection: Optional[NeonDBConnection] = None


def get_db_connection() -> NeonDBConnection:
    """
    Get singleton database connection instance
    
    Returns:
        Database connection instance
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = NeonDBConnection()
    
    return _db_connection


def close_db_connection():
    """Close the singleton database connection"""
    global _db_connection
    
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None
