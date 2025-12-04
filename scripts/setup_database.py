"""
One-time database setup script for Railway deployment.
Run this after deploying to initialize schema and procedures.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db

def setup_database():
    """Initialize database schema and procedures"""
    print("=" * 60)
    print("Setting up database schema and procedures...")
    print("=" * 60)
    
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
    procedures_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'procedures.sql')
    
    if not os.path.exists(schema_path):
        print(f"ERROR: schema.sql not found at {schema_path}")
        return False
    
    if not os.path.exists(procedures_path):
        print(f"ERROR: procedures.sql not found at {procedures_path}")
        return False
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    with open(procedures_path, 'r', encoding='utf-8') as f:
        procedures_sql = f.read()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            print("\nExecuting schema.sql...")
            statements = [s.strip() for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]
            for i, statement in enumerate(statements, 1):
                try:
                    cursor.execute(statement)
                    if i % 10 == 0:
                        print(f"  Processed {i} statements...")
                except Exception as e:
                    error_str = str(e).lower()
                    if 'already exists' in error_str or 'duplicate' in error_str:
                        pass
                    else:
                        print(f"  [WARN] Statement {i}: {str(e)[:100]}")
            
            conn.commit()
            print("  [OK] Schema executed")
            
            print("\nExecuting procedures.sql...")
            procedure_blocks = procedures_sql.split('DELIMITER //')
            for block in procedure_blocks:
                if not block.strip() or block.strip().startswith('--'):
                    continue
                
                statements = [s.strip() for s in block.split('//') if s.strip() and not s.strip().startswith('DELIMITER')]
                for statement in statements:
                    if not statement or statement.startswith('--'):
                        continue
                    try:
                        cursor.execute(statement.replace('//', ';'))
                    except Exception as e:
                        error_str = str(e).lower()
                        if 'already exists' in error_str or 'duplicate' in error_str:
                            pass
                        else:
                            proc_name = statement[:50] if len(statement) > 50 else statement
                            print(f"  [WARN] Procedure: {proc_name}... - {str(e)[:100]}")
            
            conn.commit()
            cursor.close()
            print("  [OK] Procedures executed")
            
            print("\n" + "=" * 60)
            print("Database setup complete!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"\n[ERROR] Failed to setup database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)

