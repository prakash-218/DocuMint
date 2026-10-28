import io

import pytest
from werkzeug.datastructures import FileStorage

from projects import UploadError, document_families, project_label, project_money, read_upload, suggest_title


def _doc(i, doc_type='quote', source=None, customer='c1', number=None, base=None, **extra):
    return {'invoice_id': i, 'doc_type': doc_type, 'source_invoice_id': source, 'customer_id': customer,
            'doc_number': number or i, 'base_number': base, **extra}


def test_families_follow_conversions_and_revisions():
    rows = [
        _doc('q1', number='Q/027'),
        _doc('q1r1', number='Q/027 Rev.1', base='Q/027', source='q1'),
        _doc('q1r2', number='Q/027 Rev.2', base='Q/027'),                # revision without a source link
        _doc('pi', 'proforma', source='q1r2'),
        _doc('inv', 'invoice', source='pi'),
        _doc('q2', number='Q/028'),                                       # unrelated quote
        _doc('other', 'invoice', source='q2', customer='c2'),             # different customer: never joined
    ]
    families = sorted(sorted(f) for f in document_families(rows))
    assert families == [['inv', 'pi', 'q1', 'q1r1', 'q1r2'], ['other'], ['q2']]


def test_same_quote_number_for_two_customers_stays_apart():
    rows = [_doc('a', number='Q/001'), _doc('b', number='Q/001', customer='c2')]
    assert len(document_families(rows)) == 2


def test_suggest_title_prefers_quote_subject():
    docs = [_doc('inv', 'invoice', number='029', issue_date='2026-06-01'),
            _doc('q', number='Q/027', subject='Shaft main drive tool', issue_date='2026-05-01')]
    assert suggest_title(docs) == 'Shaft main drive tool'
    assert suggest_title([_doc('inv', 'invoice', number='029', subject='null')]) == 'Work from 029'
    assert project_label({'project_no': 7}) == 'PRJ-007'


def _file(name, data):
    return FileStorage(stream=io.BytesIO(data), filename=name)


def test_upload_checks():
    assert read_upload(_file('PO 4471.pdf', b'%PDF-1.7 ...'))[:2] == ('PO 4471.pdf', 'application/pdf')
    assert read_upload(_file('C:\\scans\\drawing.DWG', b'AC1032'))[:2] == ('drawing.DWG', 'application/acad')
    with pytest.raises(UploadError, match='supported'):
        read_upload(_file('evil.html', b'<script>'))
    with pytest.raises(UploadError, match='real .pdf'):
        read_upload(_file('fake.pdf', b'<html>'))
    with pytest.raises(UploadError, match='empty'):
        read_upload(_file('empty.txt', b''))
    with pytest.raises(UploadError, match='under 10 MB'):
        read_upload(_file('big.zip', b'PK' + b'0' * (10 * 1024 * 1024)))


def test_project_money_per_currency():
    docs = [
        _doc('q0', status='revised', total_amount=900, currency_code='INR'),
        _doc('q1', status='accepted', total_amount=1000, currency_code='INR'),
        _doc('pi', 'proforma', status='sent', total_amount=1180, currency_code='INR'),
        _doc('i1', 'invoice', status='pending', total_amount=1180, paid_amount=500, currency_code='INR'),
        _doc('e1', 'export_invoice', status='paid', total_amount=300, paid_amount=300, currency_code='USD'),
        _doc('d1', 'invoice', status='draft', total_amount=50, currency_code='INR'),
    ]
    money = project_money(docs)
    assert money['quoted'] == {'INR': 1000}
    assert money['invoiced'] == {'INR': 1180, 'USD': 300}
    assert money['received'] == {'INR': 500, 'USD': 300}
    assert money['due'] == {'INR': 680}


def _project(no, title, customer='Wipro Hydraulics Private Limited', site='', status='open', fy='26-27', reference=''):
    return {'project_id': f'p{no}', 'project_no': no, 'title': title, 'customer_name': customer, 'customer_site': site,
            'status': status, 'fiscal_year': fy, 'reference': reference}


def test_finding_a_project_forgives_typos_and_abbreviations():
    from projects import match_score, search_projects
    rows = [_project(47, 'Piston torque fix', site='A22'), _project(49, 'Burnishing shaft Ø47 (PO 94385456)', site='A22'),
            _project(51, 'Piston torqueing attachment', site='C1', status='completed'),
            _project(62, 'Checking gauges', customer='Tractors and Farm Equipment Limited', site='Madurai plant')]
    found = lambda q: [p['project_no'] for p in search_projects(rows, q)]
    assert found('piston') == [47, 51]                    # open first on a tie
    assert found('pistn torqe') == [47, 51]               # a typo in each word
    assert found('trq') == [47, 51]                       # an abbreviation
    assert found('guage') == [62] and found('tafe madurai') == []   # every word must match
    assert found('tractors madurai') == [62]
    assert found('47')[0] == 47 and found('PRJ-047') == [47] and found('prj047') == [47]   # the number beats "Ø47"
    assert found('wipro a22') == [49, 47]
    assert match_score(rows[0], '') == 0 and match_score(rows[0], 'xyzzy') is None


def test_project_year_is_its_earliest_document():
    from projects import fiscal_year_of
    assert fiscal_year_of([{'fiscal_year': '26-27', 'issue_date': '2026-04-02'},
                           {'fiscal_year': '25-26', 'issue_date': '2026-03-30'}, {'fiscal_year': None}]) == '25-26'
    assert fiscal_year_of([{'issue_date': '2026-04-02'}]) is None


def test_recent_years(monkeypatch):
    import projects
    monkeypatch.setattr(projects, 'current_fiscal_year', lambda org_id: '26-27')
    assert projects.recent_fiscal_years('o') == ['26-27', '25-26', '24-25']
    monkeypatch.setattr(projects, 'current_fiscal_year', lambda org_id: '00-01')
    assert projects.recent_fiscal_years('o', 2) == ['00-01', '99-00']
    monkeypatch.setattr(projects, 'current_fiscal_year', lambda org_id: '2026')
    assert projects.recent_fiscal_years('o', 2) == ['2026', '2025']
