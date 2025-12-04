"""
Extract schema and procedures from MySQL dump file and update schema.sql and procedures.sql
"""

import sys
import os
import re

def extract_schema_from_dump(dump_path):
    """Extract CREATE TABLE statements from dump file"""
    print("Extracting schema from dump...")
    
    with open(dump_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all CREATE TABLE statements
    # Pattern: from "-- Table structure for table" to the end of CREATE TABLE
    table_pattern = r'--\s*Table structure for table `([^`]+)`.*?(CREATE TABLE[^;]+;)'
    
    tables = {}
    for match in re.finditer(table_pattern, content, re.DOTALL | re.IGNORECASE):
        table_name = match.group(1)
        create_statement = match.group(2)
        
        # Clean up MySQL-specific comments
        create_statement = re.sub(r'/\*!.*?\*/', '', create_statement, flags=re.DOTALL)
        create_statement = re.sub(r'/\*.*?\*/', '', create_statement, flags=re.DOTALL)
        
        # Remove DROP TABLE statements
        create_statement = re.sub(r'DROP TABLE IF EXISTS[^;]+;', '', create_statement, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        create_statement = re.sub(r'\s+', ' ', create_statement)
        create_statement = create_statement.strip()
        
        if create_statement:
            tables[table_name] = create_statement
    
    # Build schema.sql content
    schema_lines = []
    schema_lines.append("-- Database schema extracted from dump")
    schema_lines.append("-- Generated automatically from data_sump.sql")
    schema_lines.append("")
    
    # Order tables by dependencies (simple ordering)
    table_order = [
        'users', 'person', 'organization', 'user_organization',
        'customer', 'customer_user', 'customer_contact_assignment',
        'template', 'section', 'field',
        'invoice', 'invoice_value', 'payment'
    ]
    
    # Add tables in order, then any remaining tables
    added = set()
    for table_name in table_order:
        if table_name in tables:
            schema_lines.append(tables[table_name] + ';')
            schema_lines.append("")
            added.add(table_name)
    
    # Add any remaining tables
    for table_name, create_statement in tables.items():
        if table_name not in added:
            schema_lines.append(create_statement + ';')
            schema_lines.append("")
    
    return '\n'.join(schema_lines)


def extract_procedures_from_dump(dump_path):
    """Extract CREATE PROCEDURE statements from dump file"""
    print("Extracting procedures from dump...")
    
    with open(dump_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start of procedures section
    proc_start = content.find('-- Dumping routines for database')
    if proc_start == -1:
        print("Warning: Could not find procedures section")
        return ""
    
    proc_content = content[proc_start:]
    
    # Extract procedure blocks
    procedures = []
    
    # Pattern to find procedure definitions
    # Each procedure starts with DROP PROCEDURE IF EXISTS and ends with DELIMITER ;
    proc_pattern = r'/\*!50003 DROP PROCEDURE IF EXISTS `([^`]+)` \*/.*?DELIMITER ;;.*?(CREATE[^;]+END ;;).*?DELIMITER ;'
    
    for match in re.finditer(proc_pattern, proc_content, re.DOTALL | re.IGNORECASE):
        proc_name = match.group(1)
        proc_body = match.group(2)
        
        # Clean up MySQL-specific comments
        proc_body = re.sub(r'/\*!.*?\*/', '', proc_body, flags=re.DOTALL)
        proc_body = re.sub(r'/\*.*?\*/', '', proc_body, flags=re.DOTALL)
        
        # Remove DEFINER clause
        proc_body = re.sub(r'CREATE\s+DEFINER=`[^`]+`@`[^`]+`\s+PROCEDURE', 'CREATE PROCEDURE', proc_body, flags=re.IGNORECASE)
        
        # Replace DELIMITER ;; with DELIMITER //
        proc_body = proc_body.replace('DELIMITER ;;', 'DELIMITER //')
        proc_body = proc_body.replace('END ;;', 'END //')
        proc_body = proc_body.replace('DELIMITER ;', 'DELIMITER //')
        
        # Clean up extra whitespace but preserve structure
        lines = proc_body.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('/*!') and not line.startswith('/*'):
                cleaned_lines.append(line)
        
        proc_body = '\n'.join(cleaned_lines)
        
        # Ensure proper DELIMITER format
        if not proc_body.startswith('DELIMITER //'):
            proc_body = 'DELIMITER //\n' + proc_body
        if not proc_body.endswith('//'):
            proc_body = proc_body.rstrip() + '\n//'
        
        procedures.append((proc_name, proc_body))
    
    # Build procedures.sql content
    proc_lines = []
    proc_lines.append("-- Stored procedures extracted from dump")
    proc_lines.append("-- Generated automatically from data_sump.sql")
    proc_lines.append("")
    
    for proc_name, proc_body in sorted(procedures):
        proc_lines.append(f"DROP PROCEDURE IF EXISTS {proc_name} //")
        proc_lines.append("")
        proc_lines.append(proc_body)
        proc_lines.append("")
    
    return '\n'.join(proc_lines)


def main():
    dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_sump.sql')
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
    procedures_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'procedures.sql')
    
    if not os.path.exists(dump_path):
        print(f"Error: {dump_path} not found")
        sys.exit(1)
    
    print("=" * 60)
    print("Extracting Schema and Procedures from Dump")
    print("=" * 60)
    
    # Extract schema
    schema_content = extract_schema_from_dump(dump_path)
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(schema_content)
    print(f"  [OK] Updated {schema_path}")
    
    # Extract procedures
    procedures_content = extract_procedures_from_dump(dump_path)
    if procedures_content:
        with open(procedures_path, 'w', encoding='utf-8') as f:
            f.write(procedures_content)
        print(f"  [OK] Updated {procedures_path}")
    else:
        print("  [WARN] No procedures extracted")
    
    print("\n" + "=" * 60)
    print("Extraction complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

