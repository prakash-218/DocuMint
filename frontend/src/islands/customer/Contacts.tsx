import { useState } from 'react';
import { Icon } from '../../icons';
import { ContactForm, type ContactFields } from '../project/People';
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

/** The customer's people (a site's include its parent company's), and what each usually gets by email. */
export function Contacts({ people, usually, canEdit, name, onSave, onDelete }: Props) {
  const [editing, setEditing] = useState<string | null>(null);     // a contact_id, or 'new'
  const form = (initial: Partial<ContactFields>, label: string) => (
    <ContactForm initial={initial} usually={usually} submitLabel={label} onCancel={() => setEditing(null)}
                 onSubmit={async (f) => { const ok = await onSave(f); if (ok) setEditing(null); return ok; }} />
  );

  return (
    <section className="card pp-card" aria-labelledby="cp-people">
      <div className="card-header pp-card-head">
        <h2 className="card-title" id="cp-people">People</h2>
        {canEdit && editing === null && (
          <button type="button" className="btn btn-ghost btn-xs" onClick={() => setEditing('new')}><Icon name="userPlus" size={14} />Add</button>
        )}
      </div>
      {people.length === 0 && editing !== 'new' && (
        <div className="card-body"><p className="text-tertiary pp-empty">No contacts at {name} yet.</p></div>
      )}
      {people.length > 0 && (
        <ul className="pp-people">
          {people.map((p) => (
            <li key={p.contact_id} className={p.gets === 'none' ? 'is-off' : ''}>
              {editing === p.contact_id ? (
                <div className="cp-edit">
                  {form({ contact_id: p.contact_id, customer_id: p.customer_id, name: p.name, email: p.email ?? '',
                          phone: p.phone ?? '', role: p.role ?? '', gets: p.gets }, 'Save')}
                </div>
              ) : (
                <>
                  <span className="pp-avatar" aria-hidden="true">{p.initials}</span>
                  <div className="pp-person-name">{p.name}{p.role && <span className="text-tertiary"> · {p.role}</span>}</div>
                  <div className="pp-person-sub">{[p.email, p.phone].filter(Boolean).join(' · ')}</div>
                  <div className="pp-person-sub">{usually[p.gets]}{p.at_parent ? ' · parent company' : ''}</div>
                  {canEdit && editing === null && (
                    <div className="cp-person-actions">
                      <button type="button" className="btn btn-ghost btn-xs" onClick={() => setEditing(p.contact_id)}
                              aria-label={`Edit ${p.name}`}><Icon name="pencil" size={14} /></button>
                      <button type="button" className="btn btn-ghost btn-xs" aria-label={`Remove ${p.name}`}
                              onClick={() => { if (window.confirm(`Remove ${p.name} from the contacts?`)) onDelete(p); }}>
                        <Icon name="trash" size={14} />
                      </button>
                    </div>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      {editing === 'new' && <div className="card-body pp-add">{form({}, 'Add contact')}</div>}
    </section>
  );
}
