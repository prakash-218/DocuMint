import { useState, type CSSProperties } from 'react';
import { Composer } from '../EmailComposer';
import { NextStep, Tracker } from '../project/Overview';
import type { Page, Step } from '../project/types';
import '../project/project.css';
import './document.css';

// The top of the new document page (templates/invoices/new_view.html): where the quotation, proforma or invoice
// is, and what to do next (document_view.py). The document, its money and its forms are the page below.

interface Props {
  next: Page['next'];
  steps: Step[];
  invoiceId: string;
  /** Its project: the email form goes by the project, so without one there's no email action. */
  projectId: string | null;
}

export default function DocumentNext({ next, steps, invoiceId, projectId }: Props) {
  const [composing, setComposing] = useState(false);
  const [notice, setNotice] = useState('');
  return (
    <div className="pp doc-next">
      <div style={{ '--steps': steps.length } as CSSProperties}>
        <Tracker steps={steps} />
      </div>
      <NextStep next={next} onEmail={() => setComposing(true)} onStatus={() => undefined} />
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
