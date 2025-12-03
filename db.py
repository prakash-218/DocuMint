"""
Database connection and stored procedure execution module.
All database operations must go through stored procedures.
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import os
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
# Use explicit path to ensure .env is found
import pathlib
env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass


class Database:
    """Database connection pool manager"""
    
    def __init__(self):
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool from environment variables"""
        # Ensure .env is loaded (in case this is called before app initialization)
        load_dotenv()
        
        self.pool = pymysql.connections.Connection(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'invoice_generator'),
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=False
        )
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        try:
            # For simplicity, we'll use a single connection
            # In production, use a proper connection pool like PyMySQLPool
            if self.pool is None or not self.pool.open:
                self._initialize_pool()
            yield self.pool
        except Exception as e:
            if self.pool:
                self.pool.rollback()
            raise DatabaseError(f"Database connection error: {str(e)}")
        finally:
            # Keep connection open for reuse
            pass
    
    def execute_proc(self, proc_name: str, args: tuple = None, fetch: bool = True) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a stored procedure and return results.
        
        Args:
            proc_name: Name of the stored procedure
            args: Tuple of arguments to pass to the procedure
            fetch: Whether to fetch results (True) or just execute (False)
        
        Returns:
            List of dictionaries (rows) if fetch=True, None otherwise
            For procedures returning multiple result sets, returns a list of result sets
        """
        if args is None:
            args = ()
        
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.callproc(proc_name, args)
                
                if not fetch:
                    conn.commit()
                    cursor.close()
                    return None
                
                # Fetch all result sets
                results = []
                while True:
                    result = cursor.fetchall()
                    if result:
                        results.append(result)
                    if not cursor.nextset():
                        break
                
                conn.commit()
                cursor.close()
                
                # If single result set, return it directly; otherwise return list of result sets
                if len(results) == 0:
                    return None
                elif len(results) == 1:
                    return results[0]
                else:
                    return results
                    
            except pymysql.Error as e:
                conn.rollback()
                error_msg = str(e)
                # Extract MySQL error code and message
                if hasattr(e, 'args') and len(e.args) > 1:
                    error_code = e.args[0]
                    error_msg = e.args[1]
                raise DatabaseError(f"Stored procedure error in {proc_name} (Code: {getattr(e, 'args', [None])[0] if hasattr(e, 'args') and len(e.args) > 0 else 'Unknown'}): {error_msg}")
            except Exception as e:
                conn.rollback()
                import traceback
                raise DatabaseError(f"Unexpected error executing {proc_name}: {str(e)}\n{traceback.format_exc()}")
    
    def execute_proc_single(self, proc_name: str, args: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute a stored procedure and return a single row.
        
        Args:
            proc_name: Name of the stored procedure
            args: Tuple of arguments to pass to the procedure
        
        Returns:
            Single dictionary (row) or None if no results
        """
        results = self.execute_proc(proc_name, args, fetch=True)
        if results and len(results) > 0:
            return results[0]
        return None
    
    def execute_proc_with_id(self, proc_name: str, args: tuple = None) -> Optional[str]:
        """
        Execute a stored procedure that returns an ID (common pattern).
        The procedure should return the ID as the first column of the first row.
        
        Args:
            proc_name: Name of the stored procedure
            args: Tuple of arguments to pass to the procedure
        
        Returns:
            ID string or None
        """
        result = self.execute_proc_single(proc_name, args)
        if result:
            # Return the first value (assuming it's the ID)
            return list(result.values())[0] if result else None
        return None


# Global database instance
db = Database()

