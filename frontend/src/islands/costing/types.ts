// GET /api/costings/<id> (costing_view.editor) and /api/costings/rates (costing_view.rates_page). The sheet is kept as
// typed (strings); the server works out every number (costing.compute) and sends them back as a Result.

export interface Line {
  description: string;
  make: string;
  qty: string;
  unit: string;
  unit_cost: string;
  markup: string;
}

export interface Item {
  key: string;               // how shared costs name the items they're spread over, and how results find their row
  name: string;
  description: string;
  qty: string;
  unit: string;
  cost_each: string;         // typed; with cost lines the cost is their total instead
  profit_percent: string;
  price_each: string;        // typed to set a price; empty to work it out
  lines: Line[];
}

export interface Shared {
  description: string;
  kind: string;              // 'amount' or 'percent' (of the items' cost)
  qty: string;
  unit_cost: string;
  markup: string;
  percent: string;
  spread: string;            // 'equal' or 'cost'
  items: string[];           // item keys; none = all items
}

export interface Settings {
  mode: string;
  profit_percent: string;
  target_total: string;
  round_to: string;
  currency: string;
  exchange_rate: string;
}

export interface Totals {
  cost: number;
  cost_base: number;
  shared: number;
  price: number;
  profit: number;
  profit_on_cost: number | null;
  margin_of_price: number | null;
  target?: number;
  budget?: number | null;
  left?: number | null;
  off_target?: number;
}

export interface ResultItem {
  key: string;
  own_cost_each: number;
  shared_each: number;
  price: number;
  amount: number;
  profit: number;
  profit_on_cost: number | null;
  manual_price: boolean;
  lines: { cost: number }[];
}

export interface Result {
  mode: string;
  profit_percent: number;
  round_to: number;
  items: ResultItem[];
  shared: { amount: number }[];
  totals: Totals;
  currency: string;
  needs_rate: boolean;
}

export interface Rate {
  description: string;
  make: string;
  unit: string;
  unit_cost: number | null;
  markup: number | null;
  notes?: string;
}

/** A number as stored, the way the inputs show it: up to 4 decimals, no trailing zeros */
type Stored = number | string | null | undefined;

export interface StoredSheet {
  items: { key: string; name: string; description: string; qty: Stored; unit: string; cost_each: Stored; profit_percent: Stored;
           price_each: Stored; lines: Record<keyof Line, Stored>[] }[];
  shared: (Record<'description' | 'kind' | 'qty' | 'unit_cost' | 'markup' | 'percent' | 'spread', Stored> & { items: string[] })[];
  exchange_rate: Stored;
}

export interface CostingData {
  title: string;
  tab: string;
  costing: {
    id: string; version: number; title: string; notes: string; customer: string;
    project: { label: string; title: string; url: string };
    quote: { url: string; number: string; status: string } | null;
  };
  sheet: StoredSheet;
  settings: { mode: string; profit_percent: number; target_total: number | null; round_to: number; currency: string };
  result: Result;
  base: string;
  options: { modes: [string, string][]; rounding: number[]; currencies: string[]; spreads: [string, string][]; shared_kinds: [string, string][] };
  templates: { id: string; name: string }[];
  versions: { url: string; version: number; total: number; currency: string; profit_on_cost: number | null; quote_number: string }[];
  rates: Rate[];
  urls: { save: string; preview: string; library: string; items: string; import: string; rates: string; new_version: string;
          delete: string; project_id: string;
          /** A purchase order of some of its lines (null: they may not make one). */
          purchase_order?: string | null };
}
