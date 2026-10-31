import { useState, type FormEvent, type MouseEvent } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { PageHeader } from '../../app/PageHeader';
import { EmptyState, Filters, Loading, Pager, useLoad } from '../../app/ui';
import { Icon } from '../../icons';
import type { CustomerList as Data, CustomerRow } from './types';

// The customers (or the suppliers: the same companies, one can be both), a company's sites under it, a page at a time;
// ?q= searches (the server keeps a matching site's parent and a matching parent's sites), ?include_archived=true shows
// archived ones too.

/** A row is a link: a click anywhere on it opens the customer, as the server page's rows did */
function openRow(e: MouseEvent<HTMLTableRowElement>) {
  if (!(e.target as Element).closest('a, button, input')) e.currentTarget.querySelector('a')?.click();
}

function Row({ c }: { c: CustomerRow }) {
  return (
    <tr onClick={openRow} className={[c.archived && 'row-muted', c.site && 'row-site'].filter(Boolean).join(' ') || undefined}
        style={{ cursor: 'pointer' }}>
      <td>
        <a href={c.url} className="cell-primary" style={{ color: 'inherit' }}>{c.name}</a>
        <span className="cell-secondary">{c.sub}</span>
      </td>
      <td className="hide-mobile">{c.tax_id || '—'}</td>
      <td className="num">{c.documents}</td>
    </tr>
  );
}

function List({ data }: { data: Data }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [query, setQuery] = useState(data.query);
  function search(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (data.archived) params.set('include_archived', 'true');
    if (query.trim()) params.set('q', query.trim());
    const q = params.toString();
    navigate(location.pathname + (q ? `?${q}` : ''));
  }
  return (
    <>
      <PageHeader title={data.title}
                  actions={data.new && <a href={data.new} className="btn btn-primary"><Icon name="plus" /><span className="btn-label">{data.new_label}</span></a>} />
      <Filters filters={data.filters}>
        <form className="search-input" role="search" onSubmit={search}>
          <Icon name="search" />
          <label htmlFor="q" className="sr-only">Search</label>
          <input type="search" id="q" name="q" value={query} onChange={(e) => setQuery(e.target.value)} className="form-input"
                 placeholder="Search name, city or GSTIN" />
        </form>
      </Filters>
      <div className="card">
        {data.groups.length ? (
          <>
            <div className="table-container" style={{ border: 0, boxShadow: 'none' }}>
              <table className="table">
                <thead><tr><th>Name</th><th className="hide-mobile">GSTIN / Tax ID</th><th className="num">Documents</th></tr></thead>
                <tbody>
                  {data.groups.flatMap((g) => [g.customer, ...g.sites]).map((c) => <Row key={c.id} c={c} />)}
                </tbody>
              </table>
            </div>
            <Pager page={data.page} />
          </>
        ) : data.query ? <EmptyState icon="search" title={`No ${data.title.toLowerCase()} match`} />
          : data.kind === 'supplier'
            ? <EmptyState icon="truck" title="No suppliers yet" action={data.new ? { href: data.new, label: data.new_label } : null} />
            : <EmptyState icon="users" title="No customers yet" action={data.new ? { href: data.new, label: data.new_label } : null} />}
      </div>
    </>
  );
}

export default function CustomerList({ search, kind = 'customer' }: { search: string; kind?: 'customer' | 'supplier' }) {
  const params = new URLSearchParams(search);
  if (kind === 'supplier') params.set('kind', 'supplier');
  const query = params.toString();
  const what = kind === 'supplier' ? 'suppliers' : 'customers';
  const { data, error } = useLoad<Data>(`/api/customers${query ? `?${query}` : ''}`, `Couldn't load the ${what}. Check your connection.`);
  return data ? <List data={data} /> : <Loading title={kind === 'supplier' ? 'Suppliers' : 'Customers'} kind="list" error={error} />;
}
