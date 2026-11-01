"""
Advances: money received against a proforma before there's an invoice.

An advance is recorded on the proforma, and moves to the invoice it's applied to: when the
proforma is converted, its advances go with it; an invoice can also take any advance still on
the same customer's proformas (a job billed from two PIs). Moving rather than copying keeps
each rupee counted once, and the payment remembers its proforma (payment.advance_of).
"""

from typing import Dict, List, Optional

from db import db


def on_proforma(proforma_id) -> List[Dict]:
    """Every advance received on the proforma, applied or not."""
    return db.execute_proc('sp_list_advances', (proforma_id,)) or []


def open_for(invoice: Dict, org_id) -> List[Dict]:
    """Advances on the customer's proformas that an invoice could take: same currency, the
    invoice's project first."""
    rows = db.execute_proc('sp_list_open_advances', (org_id, invoice['customer_id'], invoice.get('currency_code'))) or []
    same = invoice.get('project_id')
    return sorted(rows, key=lambda r: (not same or r.get('project_id') != same, str(r.get('payment_date') or '')))


def apply(org_id, invoice_id, payment_ids) -> int:
    for payment_id in payment_ids:
        db.execute_proc('sp_apply_advance', (payment_id, invoice_id, org_id), fetch=False)
    return len(payment_ids)


def carry_over(org_id, proforma_id, invoice_id, limit: Optional[float] = None) -> float:
    """A proforma converted to an invoice: its advances not applied elsewhere go to the invoice. With a limit (an
    invoice for part of it), only the advances that fit in it, in the order they came; the rest wait for the next."""
    waiting = [a for a in on_proforma(proforma_id) if not a.get('applied')]
    if limit is not None:
        fits, held = [], 0.0
        for a in waiting:
            if held + float(a['amount'] or 0) <= limit + 0.005:
                fits.append(a)
                held += float(a['amount'] or 0)
        waiting = fits
    apply(org_id, invoice_id, [a['payment_id'] for a in waiting])
    return sum(float(a['amount'] or 0) for a in waiting)
