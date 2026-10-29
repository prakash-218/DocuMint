import { useState } from 'react';
import { money as fmt } from '../../format';
import { Composer } from '../EmailComposer';
import { NextStep, Tracker } from '../project/Overview';
import type { Page, Step, Tone } from '../project/types';
import './document.css';

// The top of the new document page (templates/invoices/new_view.html), as the prototype draws it: the number,
// what it is and for whom, its state; what to do next (document_view.py); and its money. The document itself,
// its payments and forms are the page below.

export interface Head {
  number: string;
  kind: string;
  customer: { name: string; url: string };
  project: { label: string; title: string; url: string } | null;
  pill: { text: string; tone: Tone };
}

interface Props {
  next: Page['next'];
  steps?: Step[];
  head?: Head;
  /** Under the next step: four amounts (document_view.money_strip); none for a quotation. */
  money?: { label: string; value: number; cap: string; late?: boolean }[] | null;
  currency?: string;
  invoiceId: string;
  /** Its project: the email form goes by the project, so without one there's no email action. */
  projectId: string | null;
}

export default function DocumentNext({ next, steps, head, money, currency = 'INR', invoiceId, projectId }: Props) {
  const [composing, setComposing] = useState(false);
  const [notice, setNotice] = useState('');
  return (
    <div className="ui doc-next">
      {head ? (
        <header className="head">
          <div>
            <h1 className="mono">{head.number}</h1>
            <div className="meta">
              <span>{head.kind}</span>
              <a href={head.customer.url}>{head.customer.name}</a>
              {head.project && <a href={head.project.url}><span className="mono">{head.project.label}</span> {head.project.title}</a>}
            </div>
          </div>
          <div className="head-right"><span className={`pill tone-${head.pill.tone}`}>{head.pill.text}</span></div>
        </header>
      ) : steps && <Tracker steps={steps} />}
      <NextStep next={next} onEmail={() => setComposing(true)} onStatus={() => undefined} />
      {money && (
        <section className="money" aria-label="The money">
          {money.map((m) => (
            <div key={m.label} className={m.late ? 'due-late' : ''}>
              <small>{m.label}</small><b>{m.value < 0 ? `−${fmt(-m.value, currency)}` : fmt(m.value, currency)}</b>
              {m.cap && <span className="cap">{m.cap}</span>}
            </div>
          ))}
        </section>
      )}
      {composing && projectId && (
        <Composer projectId={projectId} invoiceId={invoiceId}
                  onClose={(sent) => {
                    setComposing(false);
                    if (sent) setNotice('Email sent. It shows on the project page.');
                  }} />
      )}
      {notice && <p className="doc-next-notice" role="status">{notice}</p>}
    </div>
  );
}
