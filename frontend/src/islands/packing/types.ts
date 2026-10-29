// GET /api/packing/<id> (packing_page.py): a document's packing, box by box.

export interface BoxField {
  key: string;
  label: string;
  sum: boolean;            // added up across the boxes on the packing list (weights)
}

export interface PackLine {
  ordinal: number;         // the line's own number, which the form's qty_<box>_<ordinal> uses
  sl: number;
  label: string;
  hsn: string;
  qty: number;
  unit: string;
}

export interface PackingData {
  title: string;
  number: string;
  customer: string;
  back: string;
  pdf: { href: string; label: string };
  action: string;
  packing_list_no: string;
  marks: string;
  box_fields: BoxField[];
  lines: PackLine[];
  boxes: { values: Record<string, string>; packed: Record<string, number> }[];
  unpacked: { label: string; qty: number }[];   // as saved: what isn't in a box yet
  over: { label: string; qty: number }[];       // and what's packed more than invoiced
}
