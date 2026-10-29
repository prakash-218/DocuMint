import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Icon } from '../../icons';
import { blankItem, money, num } from './sheet';
import type { Item, Line } from './types';

// Adding rows to a costing from elsewhere: items copied from an earlier costing (costings_bp.library, .items), or rows
// picked out of a spreadsheet (costings_bp.read_spreadsheet reads the workbook into grids; the mapping is done here).

function Dialog({ open, onClose, id, title, wide, children, foot }: {
  open: boolean; onClose: () => void; id: string; title: string; wide?: boolean; children: ReactNode; foot: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      if (d.showModal) d.showModal();
      else d.setAttribute('open', '');
    } else if (!open && d.open) {
      if (d.close) d.close();
      else d.removeAttribute('open');
    }
  }, [open]);
  return (
    <dialog ref={ref} className={`k-dialog${wide ? ' k-dialog-wide' : ''}`} id={id} aria-labelledby={`${id}-title`}
            onClose={onClose} onClick={(e) => { if (e.target === ref.current) onClose(); }}>
      <div className="k-dialog-head">
        <h2 id={`${id}-title`}>{title}</h2>
        <button type="button" className="btn btn-ghost btn-xs" aria-label="Close" onClick={onClose}><Icon name="x" /></button>
      </div>
      <div className="k-dialog-body">{children}</div>
      <div className="k-dialog-foot">{foot}</div>
    </dialog>
  );
}

const stored = (v: unknown) => (v === null || v === undefined ? '' : typeof v === 'number' ? num(v) : String(v));

// ---------------------------------------------------------------- Copy from a costing

interface LibraryRow {
  costing_id: string; title: string; version: number; project: string; customer: string; items: number; total: number; currency: string;
}

interface CopyItem {
  name: string; description: string; qty: number | null; unit: string; cost_each: number | null; profit_percent: number | null;
  own_cost_each: number; lines: Record<keyof Line, unknown>[];
}

export function CopyDialog({ open, onClose, library, itemsUrl, self, onAdd }: {
  open: boolean; onClose: () => void; library: string; itemsUrl: string; self: string; onAdd: (items: Item[]) => void;
}) {
  const [query, setQuery] = useState('');
  const [rows, setRows] = useState<LibraryRow[] | null>(null);
  const [chosen, setChosen] = useState<{ row: LibraryRow; items: CopyItem[]; cost: string } | null>(null);
  const [ticked, setTicked] = useState<boolean[]>([]);

  useEffect(() => {
    if (open) {
      setQuery('');
      setChosen(null);
    }
  }, [open]);
  useEffect(() => {
    if (!open) return undefined;
    const timer = setTimeout(() => {
      fetch(`${library}?q=${encodeURIComponent(query.trim())}`, { credentials: 'same-origin' })
        .then((r) => r.json() as Promise<LibraryRow[]>)
        .then((list) => setRows(list.filter((r) => r.costing_id !== self && r.items > 0)))
        .catch(() => setRows([]));
    }, 200);
    return () => clearTimeout(timer);
  }, [open, query, library, self]);

  function choose(row: LibraryRow) {
    fetch(itemsUrl.replace('COSTING', row.costing_id), { credentials: 'same-origin' })
      .then((r) => r.json() as Promise<{ items: CopyItem[]; cost_currency: string }>)
      .then((data) => {
        setChosen({ row, items: data.items, cost: data.cost_currency });
        setTicked(data.items.map(() => true));
      });
  }
  const count = ticked.filter(Boolean).length;
  function add() {
    if (!chosen) return;
    // Typed prices belong to that quote; here they're worked out again
    onAdd(chosen.items.filter((_, i) => ticked[i]).map((it) => ({
      ...blankItem(), name: it.name || '', description: it.description || '', qty: stored(it.qty), unit: it.unit || '',
      cost_each: it.lines.length ? '' : stored(it.cost_each), profit_percent: stored(it.profit_percent),
      lines: it.lines.map((l) => ({ description: stored(l.description), make: stored(l.make), qty: stored(l.qty), unit: stored(l.unit),
                                    unit_cost: stored(l.unit_cost), markup: stored(l.markup) })),
    })));
    onClose();
  }

  return (
    <Dialog open={open} onClose={onClose} id="k-copy" title="Copy items from a costing"
            foot={<>
              {chosen && <button type="button" className="btn btn-ghost" onClick={() => setChosen(null)}><Icon name="arrowLeft" />Other costings</button>}
              <span className="flex-grow" />
              <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
              <button type="button" className="btn btn-primary" disabled={!chosen || !count} onClick={add}>
                {chosen && count ? `Add ${count} ${count === 1 ? 'item' : 'items'}` : 'Add items'}</button>
            </>}>
      {!chosen ? (
        <div>
          <label htmlFor="k-copy-search" className="sr-only">Search costings</label>
          <input type="search" id="k-copy-search" className="form-input" placeholder="Search by title, customer or project number" autoComplete="off"
                 value={query} onChange={(e) => setQuery(e.target.value)} autoFocus />
          <ul className="pick-list k-pick">
            {(rows ?? []).map((r) => (
              <li key={r.costing_id}>
                <button type="button" className="k-pick-row" onClick={() => choose(r)}>
                  <span className="pick-main">
                    <span className="pick-title">{r.title} · v{r.version}</span>
                    <span className="pick-sub">{[r.project, r.customer, `${r.items} ${r.items === 1 ? 'item' : 'items'}`, money(r.total, r.currency)].filter(Boolean).join(' · ')}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {rows !== null && !rows.length && <p className="form-text">No costings found.</p>}
        </div>
      ) : (
        <div>
          <p className="k-dialog-sub">{chosen.row.title} · v{chosen.row.version}{chosen.row.project ? ` · ${chosen.row.project}` : ''}</p>
          <label className="k-check k-check-all">
            <input type="checkbox" checked={count === ticked.length} onChange={(e) => setTicked(ticked.map(() => e.target.checked))} /><span>All items</span>
          </label>
          <ul className="k-checklist">
            {chosen.items.map((it, i) => (
              <li key={i}>
                <label className="k-check">
                  <input type="checkbox" checked={ticked[i]} onChange={(e) => setTicked(ticked.map((v, j) => (j === i ? e.target.checked : v)))} />
                  <span>{it.name || `Item ${i + 1}`}</span>
                  <span className="k-check-sub">{[it.qty !== null ? `Qty ${it.qty}` : '', it.own_cost_each ? `${money(it.own_cost_each, chosen.cost)} each` : '',
                    it.lines.length ? `${it.lines.length} ${it.lines.length === 1 ? 'cost line' : 'cost lines'}` : ''].filter(Boolean).join(' · ')}</span>
                </label>
              </li>
            ))}
          </ul>
          <p className="form-text">Each item comes with its cost lines. Shared costs stay behind.</p>
        </div>
      )}
    </Dialog>
  );
}

// ---------------------------------------------------------------- Import from Excel

interface Sheet {
  name: string;
  rows: unknown[][];
  header_row: number | null;
  columns: Partial<Record<Column, number>>;
}
type Column = 'name' | 'spec' | 'qty' | 'unit' | 'price' | 'amount';
const COLUMNS: [Column, string][] = [['name', 'Item / description'], ['spec', 'Spec / make'], ['qty', 'Qty'], ['unit', 'Unit'],
                                     ['price', 'Unit cost or price'], ['amount', 'Amount']];
const TOTALS = /^(sub[\s-]*)?total\b|grand\s*total|^net\s*(total|amount)|^profit\b|^margin\b|^(c|s|i)?gst\b|^tax\b|^discount\b|^round(ed|ing)?\s*off/i;

const cellText = (v: unknown) => (v === null || v === undefined ? '' : String(v).trim());
function cellNumber(v: unknown): number | null {
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  const s = cellText(v).replace(/[,\s₹$]/g, '').replace(/^rs\.?/i, '');
  return /^-?\d+(\.\d+)?$/.test(s) ? parseFloat(s) : null;
}

export interface ImportRow { name: string; spec: string; qty: number | null; unit: string; price: number }

/** The rows under the heading row with an item and an amount; totals and blank rows are left out */
export function importRows(sheet: Sheet, header: number, cols: Record<Column, number>): { rows: ImportRow[]; skipped: number } {
  const at = (r: unknown[], k: Column) => (cols[k] >= 0 ? r[cols[k]] : null);
  const out: ImportRow[] = [];
  let skipped = 0;
  for (let i = header + 1; i < sheet.rows.length; i++) {
    const r = sheet.rows[i];
    let name = cellText(at(r, 'name'));
    let spec = cellText(at(r, 'spec'));
    const unit = cellText(at(r, 'unit'));
    const qty = cellNumber(at(r, 'qty'));
    let price = cellNumber(at(r, 'price'));
    const amount = cellNumber(at(r, 'amount'));
    if (!name && !spec && qty === null && price === null && amount === null) continue;   // blank rows don't count
    if (!name && spec) {
      name = spec;
      spec = '';
    }
    if (!name || TOTALS.test(name) || (price === null && amount === null)) {
      skipped += 1;
      continue;
    }
    if (price === null) price = qty ? (amount as number) / qty : (amount as number);
    out.push({ name, spec, qty, unit, price: Math.round(price * 10000) / 10000 });
  }
  return { rows: out, skipped };
}

export function ImportDialog({ open, onClose, url, base, items, onAddItems, onAddLines }: {
  open: boolean; onClose: () => void; url: string; base: string; items: string[];
  onAddItems: (items: Item[]) => void; onAddLines: (index: number, lines: Line[]) => void;
}) {
  const [file, setFile] = useState<{ file: string; sheets: Sheet[] } | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [sheetIndex, setSheetIndex] = useState(0);
  const [header, setHeader] = useState('1');
  const [cols, setCols] = useState<Record<Column, number>>({ name: -1, spec: -1, qty: -1, unit: -1, price: -1, amount: -1 });
  const [as, setAs] = useState<'items' | 'lines' | 'into'>('items');
  const [newItem, setNewItem] = useState('');
  const [into, setInto] = useState('0');
  const [prices, setPrices] = useState<'cost' | 'price'>('cost');
  const input = useRef<HTMLInputElement>(null);

  function pickSheet(sheets: Sheet[], i: number) {
    const s = sheets[i];
    setSheetIndex(i);
    setHeader(String((s.header_row ?? 0) + 1));
    setCols(Object.fromEntries(COLUMNS.map(([k]) => [k, s.columns[k] ?? -1])) as Record<Column, number>);
    setNewItem(s.name);
  }
  function reset() {
    setFile(null);
    setError('');
    if (input.current) input.current.value = '';
  }
  function read(chosen: File | undefined) {
    if (!chosen) return;
    setError('');
    setBusy(true);
    const body = new FormData();
    body.append('file', chosen);
    fetch(url, { method: 'POST', body, credentials: 'same-origin' })
      .then((r) => r.json().then((json) => ({ ok: r.ok, json })))
      .then(({ ok, json }) => {
        if (!ok) throw new Error(json.error || 'That file could not be read.');
        setFile(json);
        // Start on the first sheet that looks like a costing
        const first = (json.sheets as Sheet[]).findIndex((s) => s.header_row !== null && s.columns.name !== undefined);
        pickSheet(json.sheets, Math.max(0, first));
      })
      .catch((e: Error) => {
        setError(e.message);
        if (input.current) input.current.value = '';
      })
      .finally(() => setBusy(false));
  }

  const sheet = file?.sheets[sheetIndex];
  const headerRow = Math.max(0, (parseInt(header, 10) || 1) - 1);
  const got = useMemo(() => (sheet ? importRows(sheet, headerRow, cols) : { rows: [], skipped: 0 }), [sheet, headerRow, cols]);
  const width = sheet ? sheet.rows.reduce((w, r) => Math.max(w, r.length), 0) : 0;
  const heads = sheet?.rows[headerRow] ?? [];
  const mode = as === 'into' && !items.length ? 'items' : as;
  const n = got.rows.length;

  function add() {
    const lines: Line[] = got.rows.map((r) => ({ description: r.name, make: r.spec, qty: num(r.qty), unit: r.unit, unit_cost: num(r.price), markup: '' }));
    if (mode === 'items') {
      const cost = prices !== 'price';
      onAddItems(got.rows.map((r) => ({ ...blankItem(), name: r.name, description: r.spec, qty: num(r.qty), unit: r.unit,
                                         cost_each: cost ? num(r.price) : '', price_each: cost ? '' : num(r.price) })));
    } else if (mode === 'lines') {
      onAddItems([{ ...blankItem(), name: newItem.trim() || sheet?.name || '', qty: '1', lines }]);
    } else {
      onAddLines(parseInt(into, 10) || 0, lines);
    }
    onClose();
    reset();
  }

  const names = mode === 'items' ? ['Item', 'Description', 'Qty', 'Unit', prices === 'price' ? 'Price / unit' : 'Cost / unit']
    : ['Cost line', 'Make / spec', 'Qty', 'Unit', 'Unit cost'];
  return (
    <Dialog open={open} onClose={onClose} id="k-import" title="Import from Excel" wide
            foot={<>
              {file && <button type="button" className="btn btn-ghost" onClick={reset}><Icon name="arrowLeft" />Another file</button>}
              <span className="flex-grow" />
              <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
              <button type="button" className="btn btn-primary" disabled={!file || !n} onClick={add}>
                {file && n ? `Add ${n} ${mode === 'items' ? (n === 1 ? 'item' : 'items') : (n === 1 ? 'cost line' : 'cost lines')}` : 'Add rows'}</button>
            </>}>
      {!file ? (
        <div>
          <label className={`k-drop${busy ? ' busy' : ''}`}>
            <input ref={input} type="file" accept=".xlsx,.xlsm,.csv" aria-label="Workbook" onChange={(e) => read(e.target.files?.[0])} />
            <Icon name="upload" size={28} />
            <span><strong>Choose a workbook</strong> (.xlsx or .csv)</span>
            <span className="text-tertiary">It's read to pick the rows from; the file isn't kept.</span>
          </label>
          {error && <p className="form-text k-error" role="alert">{error}</p>}
        </div>
      ) : (
        <div>
          <p className="k-dialog-sub">{file.file}</p>
          <div className="k-import-grid">
            <div className="form-group">
              <label htmlFor="k-im-sheet" className="form-label">Sheet</label>
              <select id="k-im-sheet" className="form-select" value={sheetIndex} onChange={(e) => pickSheet(file.sheets, +e.target.value)}>
                {file.sheets.map((s, i) => <option key={i} value={i}>{s.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="k-im-head" className="form-label">Headings in row</label>
              <input type="number" min="1" id="k-im-head" className="form-input" value={header} onChange={(e) => setHeader(e.target.value)} />
            </div>
            {COLUMNS.map(([key, label]) => (
              <div key={key} className="form-group">
                <label htmlFor={`k-im-${key}`} className="form-label">{label}</label>
                <select id={`k-im-${key}`} className="form-select" value={cols[key] < width ? cols[key] : -1}
                        onChange={(e) => setCols({ ...cols, [key]: +e.target.value })}>
                  <option value={-1}>—</option>
                  {Array.from({ length: width }, (_, j) => {
                    const h = cellText(heads[j]);
                    return <option key={j} value={j}>{String.fromCharCode(65 + j)}{h ? ` · ${h.slice(0, 28)}` : ''}</option>;
                  })}
                </select>
              </div>
            ))}
          </div>
          <div className="k-import-as">
            <div className="form-group">
              <span className="form-label">Bring the rows in as</span>
              <label className="k-check"><input type="radio" name="k-im-as" value="items" checked={mode === 'items'} onChange={() => setAs('items')} /><span>Items, one per row</span></label>
              <label className="k-check"><input type="radio" name="k-im-as" value="lines" checked={mode === 'lines'} onChange={() => setAs('lines')} /><span>Cost lines of a new item</span>
                <input type="text" className="form-input k-im-item-name" value={newItem} placeholder="Item name" aria-label="Name of the new item"
                       onChange={(e) => setNewItem(e.target.value)} onFocus={() => setAs('lines')} /></label>
              <label className="k-check"><input type="radio" name="k-im-as" value="into" checked={mode === 'into'} disabled={!items.length} onChange={() => setAs('into')} />
                <span>Cost lines of</span>
                <select className="form-select" value={into} aria-label="The item to add the cost lines to" onChange={(e) => setInto(e.target.value)} onFocus={() => setAs('into')}>
                  {items.map((label, i) => <option key={i} value={i}>{label}</option>)}
                </select></label>
            </div>
            {mode === 'items' && (
              <div className="form-group">
                <label htmlFor="k-im-prices" className="form-label">The amounts in the price column are</label>
                <select id="k-im-prices" className="form-select" value={prices} onChange={(e) => setPrices(e.target.value as 'cost' | 'price')}>
                  <option value="cost">our costs</option>
                  <option value="price">prices to the customer</option>
                </select>
              </div>
            )}
          </div>
          <div className="k-import-preview items-wrap">
            <table className="items-editor">
              <thead><tr>{names.map((h, i) => <th key={h} className={i === 0 ? 'long' : i === 4 ? 'num' : ''}>{h}</th>)}</tr></thead>
              <tbody>
                {got.rows.slice(0, 8).map((r, i) => (
                  <tr key={i}><td className="long">{r.name}</td><td>{r.spec}</td><td>{r.qty ?? ''}</td><td>{r.unit}</td><td className="num">{money(r.price, base)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="form-text">{n
            ? `${n} ${n === 1 ? 'row' : 'rows'} to add${n > 8 ? ' (the first 8 are shown)' : ''}${got.skipped ? `. ${got.skipped} skipped: totals, or no amount.` : '.'}`
            : 'No rows with an item and an amount under that heading row. Check the sheet, the heading row and the columns.'}</p>
        </div>
      )}
    </Dialog>
  );
}
