import { Dropdown, choices } from '../../mantine/Dropdown';
import { useId, useState, type FormEvent } from 'react';
import { Icon } from '../../icons';
import type { ContactFields } from '../project/People';
import type { Contact } from './types';

interface Props {
  people: Contact[];
  usually: Record<string, string>;
  canEdit: boolean;
  /** Who they're the contacts of, for the empty message. */
  name: string;
  onSave: (fields: ContactFields) => Promise<boolean>;
  onDelete: (person: Contact) => void;
}

const fieldsOf = (p: Contact): ContactFields => ({
  contact_id: p.contact_id, customer_id: p.customer_id, name: p.name, email: p.email ?? '', phone: p.phone ?? '', role: p.role ?? '', gets: p.gets,
});

/** The customer's people (a site's include its parent company's), what each usually gets by email, and a row to add one. */
export function Contacts({ people, usually, canEdit, name, onSave, onDelete }: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  return (
    <div className="ctable">
      <div className="crow h"><span>Name</span><span>Email and phone</span><span>Role</span><span>Usually gets</span><span /></div>
      {people.length === 0 && <p className="empty-rows" style={{ borderTop: 0 }}>No contacts at {name} yet.</p>}
      {people.map((p) => editing === p.contact_id ? (
        <ContactRow key={p.contact_id} initial={fieldsOf(p)} usually={usually} submitLabel="Save" onCancel={() => setEditing(null)}
                    onSubmit={async (f) => { const ok = await onSave(f); if (ok) setEditing(null); return ok; }} />
      ) : (
        <div key={p.contact_id} className={`crow${p.gets === 'none' ? ' off' : ''}`}>
          <div className="pn">{p.name}{p.at_parent && <span> · parent company</span>}</div>
          <div className="pe">{p.email}{p.phone && <><br />{p.phone}</>}</div>
          <div className="muted">{p.role}</div>
          <div>
            {canEdit ? (
              <Dropdown size="xs" value={p.gets} aria-label={`What ${p.name} usually gets`} onChange={(v) => void onSave({ ...fieldsOf(p), gets: v })}
                        data={choices(Object.entries(usually))} />
            ) : <span className="muted">{usually[p.gets]}</span>}
          </div>
          <div className="crow-actions">
            {canEdit && editing === null && (
              <>
                <button type="button" className="btn btn-ghost btn-xs" onClick={() => setEditing(p.contact_id)} aria-label={`Edit ${p.name}`}><Icon name="pencil" size={14} /></button>
                <button type="button" className="btn btn-ghost btn-xs" aria-label={`Remove ${p.name}`}
                        onClick={() => { if (window.confirm(`Remove ${p.name} from the contacts?`)) onDelete(p); }}><Icon name="trash" size={14} /></button>
              </>
            )}
          </div>
        </div>
      ))}
      {canEdit && editing === null && (
        <ContactRow key={people.length} initial={{}} usually={usually} submitLabel="Add" onSubmit={onSave} />
      )}
    </div>
  );
}

interface RowProps {
  initial: Partial<ContactFields>;
  usually: Record<string, string>;
  submitLabel: string;
  onSubmit: (fields: ContactFields) => Promise<boolean>;
  onCancel?: () => void;
}

/** One line of inputs, the prototype's add row: name, email, phone, role (and what they get, when editing). */
function ContactRow({ initial, usually, submitLabel, onSubmit, onCancel }: RowProps) {
  const id = useId();
  const [f, setF] = useState<ContactFields>({ name: '', email: '', phone: '', role: '', gets: 'all', ...initial });
  const [saving, setSaving] = useState(false);
  const set = (k: keyof ContactFields) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    const ok = await onSubmit(f);
    setSaving(false);
    if (ok && !onCancel) setF({ name: '', email: '', phone: '', role: '', gets: 'all' });
  }

  return (
    <form className="addform" onSubmit={submit} aria-label={submitLabel === 'Add' ? 'Add a contact' : `Edit ${initial.name}`}>
      <label htmlFor={`${id}-name`} className="sr-only">Name</label>
      <input id={`${id}-name`} value={f.name} maxLength={150} placeholder="Name" onChange={set('name')} />
      <label htmlFor={`${id}-email`} className="sr-only">Email</label>
      <input id={`${id}-email`} type="email" value={f.email} maxLength={320} placeholder="Email" onChange={set('email')} />
      <label htmlFor={`${id}-phone`} className="sr-only">Phone</label>
      <input id={`${id}-phone`} type="tel" value={f.phone} maxLength={40} placeholder="Phone" onChange={set('phone')} />
      <label htmlFor={`${id}-role`} className="sr-only">Role</label>
      <input id={`${id}-role`} value={f.role} maxLength={100} placeholder="Role, e.g. Accounts" onChange={set('role')} />
      <div style={{ display: 'flex', gap: 6 }}>
        {onCancel && (
          <>
            <label htmlFor={`${id}-gets`} className="sr-only">Usually gets</label>
            <Dropdown id={`${id}-gets`} value={f.gets} onChange={(v) => set('gets')({ target: { value: v } })} data={choices(Object.entries(usually))} />
          </>
        )}
        <button type="submit" className="btn btn-secondary" disabled={saving}>{submitLabel === 'Add' && <Icon name="plus" />}{saving ? 'Saving…' : submitLabel}</button>
        {onCancel && <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  );
}
