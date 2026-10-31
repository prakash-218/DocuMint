import { useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { Icon } from '../../icons';
import { Skeleton } from '../../Skeleton';
import type { PackingData, PackLine } from './types';

// A document's packing, box by box: a column per box with its own details (the template's box fields) and how many of
// each line it holds. It posts the server page's form to invoices_bp.packing (document_service.boxes_from_form):
// box_<n>_present, box_<n>_<field>, qty_<n>_<ordinal> and box_count, n being the box's own number, so a removed box
// simply isn't posted.

interface Box {
  n: number;
  values: Record<string, string>;
  packed: Record<string, string>;
}

const amount = (v: number) => v.toLocaleString('en-US', { maximumFractionDigits: 3 });
const num = (s: string | undefined) => parseFloat(s ?? '') || 0;
const notPacked = (boxes: Box[], line: PackLine) => line.qty - boxes.reduce((sum, b) => sum + num(b.packed[line.ordinal]), 0);

export function Packing({ data }: { data: PackingData }) {
  const [boxes, setBoxes] = useState<Box[]>(() => data.boxes.map((b, i) => ({
    n: i + 1, values: b.values, packed: Object.fromEntries(Object.entries(b.packed).map(([o, q]) => [o, String(q)])),
  })));
  const highest = Math.max(...boxes.map((b) => b.n));
  const change = (n: number, part: 'values' | 'packed', key: string, value: string) =>
    setBoxes((all) => all.map((b) => (b.n === n ? { ...b, [part]: { ...b[part], [key]: value } } : b)));
  const fillRest = () => setBoxes((all) => {
    const last = all[all.length - 1];
    const packed = { ...last.packed };
    for (const line of data.lines) {
      const rest = notPacked(all, line);
      if (rest > 0) packed[line.ordinal] = String(num(packed[line.ordinal]) + rest);
    }
    return [...all.slice(0, -1), { ...last, packed }];
  });
  const mismatch = [...data.unpacked.map((l) => `${l.label}: ${amount(l.qty)} not packed yet`),
                    ...data.over.map((l) => `${l.label}: ${amount(l.qty)} more packed than invoiced`)];

  return (
    <>
      <PageHeader title={data.title} heading description={data.customer}
                  actions={<>
                    <a href={data.back} className="btn btn-ghost"><Icon name="arrowLeft" /><span className="btn-label">Back to invoice</span></a>
                    <a href={data.pdf.href} className="btn btn-secondary" target="_blank" rel="noopener">
                      <Icon name="download" /><span className="btn-label">{data.pdf.label}</span></a>
                  </>} />
      {mismatch.length > 0 && <div className="alert alert-warning"><span>{mismatch.join(' · ')}</span></div>}
      <form method="post" action={data.action} id="packingForm">
        <input type="hidden" name="box_count" value={highest} />
        <section className="card">
          <div className="card-body">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="packing_list_no" className="form-label">Packing list no.</label>
                <input type="text" id="packing_list_no" name="packing_list_no" className="form-input" defaultValue={data.packing_list_no}
                       placeholder={`PL ${data.number}`} />
              </div>
              <div className="form-group">
                <label htmlFor="marks" className="form-label">Marks &amp; nos.</label>
                <input type="text" id="marks" name="marks" className="form-input" defaultValue={data.marks}
                       placeholder={`HYDRO/PA/1-${boxes.length}`} />
              </div>
            </div>
          </div>
          <div className="table-container" style={{ border: 0, boxShadow: 'none', borderRadius: 0 }}>
            <table className="table">
              <thead>
                <tr>
                  <th style={{ minWidth: 220 }}>Item</th>
                  <th className="num">Invoiced</th>
                  {boxes.map((b, i) => (
                    <th key={b.n} style={{ minWidth: 150 }}>
                      <input type="hidden" name={`box_${b.n}_present`} value="1" />
                      <span className="flex-between" style={{ flexWrap: 'nowrap' }}>
                        <span>Box {i + 1}</span>
                        <button type="button" className="btn btn-ghost btn-xs" title="Remove box" aria-label={`Remove box ${i + 1}`}
                                disabled={boxes.length === 1} onClick={() => setBoxes((all) => all.filter((x) => x.n !== b.n))}>
                          <Icon name="x" />
                        </button>
                      </span>
                    </th>
                  ))}
                  <th className="num">Not packed</th>
                </tr>
              </thead>
              <tbody>
                {data.box_fields.map((f) => (
                  <tr key={f.key}>
                    <td className="text-secondary">{f.label}{f.sum && <span className="text-tertiary"> (totalled)</span>}</td>
                    <td />
                    {boxes.map((b, i) => (
                      <td key={b.n}>
                        <input type={f.sum ? 'number' : 'text'} step={f.sum ? 'any' : undefined} min={f.sum ? 0 : undefined}
                               name={`box_${b.n}_${f.key}`} value={b.values[f.key] ?? ''} className="form-input"
                               aria-label={`Box ${i + 1}: ${f.label}`} onChange={(e) => change(b.n, 'values', f.key, e.target.value)} />
                      </td>
                    ))}
                    <td />
                  </tr>
                ))}
                {data.lines.map((line) => {
                  const rest = notPacked(boxes, line);
                  const done = Math.abs(rest) < 1e-9;
                  return (
                    <tr key={line.ordinal}>
                      <td>
                        <span className="cell-primary" style={{ whiteSpace: 'normal' }}>{line.sl}. {line.label}</span>
                        {line.hsn && <span className="cell-secondary">HSN {line.hsn}</span>}
                      </td>
                      <td className="num">{amount(line.qty)} {line.unit}</td>
                      {boxes.map((b, i) => (
                        <td key={b.n}>
                          <input type="number" step="any" min="0" name={`qty_${b.n}_${line.ordinal}`} value={b.packed[line.ordinal] ?? ''}
                                 placeholder="0" className="form-input" aria-label={`Box ${i + 1}: ${line.label}`}
                                 onChange={(e) => change(b.n, 'packed', String(line.ordinal), e.target.value)} />
                        </td>
                      ))}
                      <td className="num" style={{ color: done ? 'var(--good-ink)' : 'var(--warning-ink)' }}>
                        {done ? '✓' : rest > 0 ? amount(rest) : `over by ${amount(-rest)}`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="card-body flex-between">
            <button type="button" className="btn btn-secondary" onClick={() => setBoxes((all) => [...all, { n: highest + 1, values: {}, packed: {} }])}>
              <Icon name="plus" />Add box
            </button>
            <div className="btn-group">
              <button type="button" className="btn btn-ghost" onClick={fillRest}>
                Put the rest in the last box
              </button>
              <button type="submit" className="btn btn-primary">Save packing</button>
            </div>
          </div>
        </section>
      </form>
    </>
  );
}

export default function PackingPage({ invoiceId }: { invoiceId: string }) {
  const [data, setData] = useState<PackingData | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    api.get<PackingData>(`/api/packing/${invoiceId}`).then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the packing. Check your connection."));
  }, [invoiceId]);

  if (!data) {
    return (
      <>
        <PageHeader title="Packing" heading />
        {error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="page" label="Loading the packing…" />}
      </>
    );
  }
  return <Packing data={data} />;
}
