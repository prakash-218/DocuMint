"""
Diagnostic script to check why dashboard data is empty
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db
import json

def diagnose_dashboard():
    """Check invoice data and total calculations"""


    with db.get_connection() as conn:
        cursor = conn.cursor()


        cursor.execute("SELECT org_id, name FROM organization LIMIT 5")
        orgs = cursor.fetchall()

        if not orgs:
            print("No organizations found")
            return

        for org in orgs:
            org_id = org['org_id']
            org_name = org['name']
            print(f"\n{'='*60}")
            print(f"Organization: {org_name} ({org_id[:8]}...)")
            print(f"{'='*60}")


            cursor.execute("""
                SELECT invoice_id, issue_date, status, total_amount, template_id, template_version
                FROM invoice
                WHERE org_id = %s
                ORDER BY issue_date DESC
                LIMIT 5
            """, (org_id,))
            invoices = cursor.fetchall()

            if not invoices:
                print("  No invoices found")
                continue

            print(f"\n  Found {len(invoices)} invoices:")
            for inv in invoices:
                inv_id = inv.get('invoice_id') or inv.get('INVOICE_ID')
                print(f"\n  Invoice {str(inv_id)[:8]}...")
                print(f"    Status: {inv.get('status') or inv.get('STATUS')}")
                print(f"    Total Amount: {inv.get('total_amount') or inv.get('TOTAL_AMOUNT')}")
                print(f"    Issue Date: {inv.get('issue_date') or inv.get('ISSUE_DATE')}")
                template_id = inv.get('template_id') or inv.get('TEMPLATE_ID')
                template_version = inv.get('template_version') or inv.get('TEMPLATE_VERSION')
                print(f"    Template: {str(template_id)[:8]}... v{template_version}")


                cursor.execute("""
                    SELECT total_field_id, name
                    FROM template
                    WHERE template_id = %s AND version = %s
                """, (template_id, template_version))
                template_info = cursor.fetchone()
                if template_info:
                    print(f"    Template Name: {template_info.get('name') or template_info.get('NAME')}")
                    total_field_id = template_info.get('total_field_id') or template_info.get('TOTAL_FIELD_ID')
                    print(f"    Template total_field_id: {total_field_id}")


                    if total_field_id:
                        cursor.execute("""
                            SELECT val_number, field_id
                            FROM invoice_value
                            WHERE invoice_id = %s AND field_id = %s
                            AND (ordinal IS NULL OR ordinal = 0)
                        """, (inv_id, total_field_id))
                        total_field_value = cursor.fetchone()
                        if total_field_value:
                            val = total_field_value.get('val_number') or total_field_value.get('VAL_NUMBER')
                            print(f"    Total Field Value: {val}")
                        else:
                            print(f"    Total Field Value: NULL (not found)")


                cursor.execute("""
                    SELECT iv.val_number, f.label, f.data_type, s.section_type, iv.ordinal
                    FROM invoice_value iv
                    JOIN field f ON iv.field_id = f.field_id
                    JOIN section s ON f.section_id = s.section_id
                    WHERE iv.invoice_id = %s
                      AND f.data_type = 'number'
                      AND (iv.ordinal IS NULL OR iv.ordinal = 0)
                    ORDER BY s.ordinal, f.ordinal
                """, (inv_id,))
                number_fields = cursor.fetchall()

                if number_fields:
                    print(f"    Number fields (normal sections, ordinal 0):")
                    for nf in number_fields:
                        label = nf.get('label') or nf.get('LABEL')
                        val = nf.get('val_number') or nf.get('VAL_NUMBER')
                        data_type = nf.get('data_type') or nf.get('DATA_TYPE')
                        section_type = nf.get('section_type') or nf.get('SECTION_TYPE')
                        print(f"      - {label}: {val} (type: {data_type}, section_type: {section_type})")
                else:
                    print(f"    No number fields found with values")


                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM invoice_value iv
                    JOIN field f ON iv.field_id = f.field_id
                    WHERE iv.invoice_id = %s
                      AND f.calculation_formula IS NOT NULL
                """, (inv_id,))
                calc_count = cursor.fetchone()
                count = calc_count.get('count') or calc_count.get('COUNT') if calc_count else 0
                print(f"    Calculated fields: {count}")


        print(f"\n{'='*60}")
        print("Dashboard Stats (using first org)")
        print(f"{'='*60}")
        if orgs:
            org_id = orgs[0]['org_id']
            stats = db.execute_proc_single('sp_get_dashboard_stats', (org_id,))
            if stats:
                print(f"\n  Stats from sp_get_dashboard_stats:")
                for key, value in stats.items():
                    print(f"    {key}: {value}")
            else:
                print("  No stats returned")

        cursor.close()

if __name__ == '__main__':
    diagnose_dashboard()

