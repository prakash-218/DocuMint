import { Dropdown, choices } from '../../mantine/Dropdown';
import { useId, useState, type FormEvent } from 'react';
import { Icon } from '../../icons';
import type { Page, Person } from './types';

export interface ContactFields {
  contact_id?: string;
  customer_id?: string;
  name: string;
  email: string;
  phone: string;
  role: string;
  gets: string;
}

interface Props {
  page: Page;
  onGets: (contactId: string, gets: string) => void;
  onSave: (fields: ContactFields) => Promise<boolean>;
  onIgnore: (value: string) => void;
}

/** The customer's contacts and what each gets on this project, and people in its emails who could be one. */
export function People({ page, onGets, onSave, onIgnore }: Props) {
  const { people, found, gets, usually, can } = page;
  const [adding, setAdding] = useState<Partial<ContactFields> | null>(null);
  const suggestions = can.read_mail && (found.people.length > 0 || found.phones.length > 0);
  const customer = page.project.customer.site || page.project.customer.name;

  return (
    <section className="side-sec" aria-labelledby="pp-people">
      <h2 id="pp-people">People
        {can.edit && !adding && (
          <button type="button" className="btn btn-secondary btn-xs" onClick={() => setAdding({})}><Icon name="userPlus" size={14} />Add</button>
        )}
      </h2>
      {people.length === 0 && !adding && <p className="muted" style={{ margin: 0 }}>No contacts at {customer} yet.</p>}
      {people.length > 0 && (
        <ul className="people">
          {people.map((p) => <PersonRow key={p.contact_id} person={p} gets={gets} canEdit={can.edit} onGets={onGets} />)}
        </ul>
      )}
      {adding && (
        <ContactForm initial={adding} usually={usually} submitLabel="Add contact" onCancel={() => setAdding(null)}
                     onSubmit={async (f) => { const ok = await onSave(f); if (ok) setAdding(null); return ok; }} />
      )}
      {suggestions && (
        <div className="found">
          <h3><Icon name="sparkles" size={14} />Found in this project's emails</h3>
          <ul className="people">
            {found.phones.map((p) => {
              const contact = people.find((x) => x.contact_id === p.contact_id);
              return (
                <li key={p.value}>
                  <div>
                    <div className="pn">Phone for {p.name}</div>
                    <div className="pe">{p.phone} · in their email signature{p.replaces ? `, saved as ${p.replaces}` : ''}</div>
                    {can.edit && contact && (
                      <div className="fa">
                        <button type="button" className="btn btn-secondary btn-xs"
                                onClick={() => void onSave({ contact_id: contact.contact_id, customer_id: contact.customer_id, name: contact.name,
                                                            email: contact.email ?? '', phone: p.phone, role: contact.role ?? '', gets: contact.usually })}>
                          Save to {contact.name}
                        </button>
                        <button type="button" className="btn btn-ghost btn-xs" onClick={() => onIgnore(p.value)}
                                aria-label={`Ignore this number for ${p.name}`}>Ignore</button>
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
            {found.people.map((p) => (
              <li key={p.email}>
                <div>
                  <div className="pn">{p.name}</div>
                  <div className="pe">{p.email}{p.phone ? ` · ${p.phone}` : ''} · {p.seen}</div>
                  {can.edit && (
                    <div className="fa">
                      <button type="button" className="btn btn-secondary btn-xs" onClick={() => setAdding({ name: p.name, email: p.email, phone: p.phone ?? '' })}>
                        Add to {customer}
                      </button>
                      <button type="button" className="btn btn-ghost btn-xs" onClick={() => onIgnore(p.email)} aria-label={`Ignore ${p.name}`}>Ignore</button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function PersonRow({ person: p, gets, canEdit, onGets }: { person: Person; gets: Record<string, string>; canEdit: boolean;
                                                           onGets: (id: string, gets: string) => void }) {
  return (
    <li className={p.gets === 'none' ? 'off' : ''}>
      <span className="avatar" aria-hidden="true">{p.initials}</span>
      <div style={{ minWidth: 0 }}>
        <div className="pn">{p.name}{p.role && <span> · {p.role}</span>}</div>
        <div className="pe">{[p.email, p.phone].filter(Boolean).join(' · ')}{p.at_parent ? ' · parent company' : ''}</div>
        {canEdit ? (
          <Dropdown size="xs" value={p.gets} aria-label={`What ${p.name} gets on this project`} onChange={(v) => onGets(p.contact_id, v)}
                    data={choices(Object.entries(gets))} />
        ) : (
          <div className="pe">{gets[p.gets]}</div>
        )}
      </div>
    </li>
  );
}

interface FormProps {
  initial: Partial<ContactFields>;
  usually: Record<string, string>;
  submitLabel: string;
  onSubmit: (fields: ContactFields) => Promise<boolean>;
  onCancel: () => void;
}

export function ContactForm({ initial, usually, submitLabel, onSubmit, onCancel }: FormProps) {
  const id = useId();
  const [f, setF] = useState<ContactFields>({ name: '', email: '', phone: '', role: '', gets: 'all', ...initial });
  const [saving, setSaving] = useState(false);
  const set = (k: keyof ContactFields) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    await onSubmit(f);
    setSaving(false);
  }

  return (
    <form className="stack-form" onSubmit={submit}>
      <label htmlFor={`${id}-name`} className="form-label">Name</label>
      <input id={`${id}-name`} className="form-input" value={f.name} maxLength={150} onChange={set('name')} />
      <label htmlFor={`${id}-role`} className="form-label">Role <span className="text-tertiary">(optional)</span></label>
      <input id={`${id}-role`} className="form-input" value={f.role} maxLength={100} placeholder="Purchase, Accounts, Plant head"
             onChange={set('role')} />
      <label htmlFor={`${id}-email`} className="form-label">Email</label>
      <input id={`${id}-email`} className="form-input" type="email" value={f.email} maxLength={320} onChange={set('email')} />
      <label htmlFor={`${id}-phone`} className="form-label">Phone <span className="text-tertiary">(optional)</span></label>
      <input id={`${id}-phone`} className="form-input" type="tel" value={f.phone} maxLength={40} onChange={set('phone')} />
      <label htmlFor={`${id}-gets`} className="form-label">Usually gets</label>
      <Dropdown id={`${id}-gets`} value={f.gets} onChange={(v) => set('gets')({ target: { value: v } })} data={choices(Object.entries(usually))} />
      <div className="form-actions-row">
        <button type="submit" className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving…' : submitLabel}</button>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}
