import { render, screen, within } from '../../test/render';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { ShareDialog, waLink, type ShareData } from './Share';

const URL = 'https://app.example/s/Zx9_long-random-token-of-forty-three-chars0';
const BODY = 'Please find our invoice TF/INV/058/26-27: ₹2,97,360 incl. GST, ₹2,97,360 due by 18 Dec 2026.\n' +
  'Pay by UPI to demoengineering@okaxis, or scan the QR code on the page.\n[link]\n\nRegards,\nDemo Engineering';

const NO_LINK: ShareData = {
  link: null, number: 'TF/INV/058/26-27', kind: 'Tax Invoice', body: BODY,
  people: [{ name: 'Mr. Karthik', role: 'Purchase', phone: '98765 43210', number: '919876543210', gets_it: true },
           { name: 'Ms. Divya', role: 'Accounts', phone: '+91 91234 56789', number: '919123456789', gets_it: false }],
  pay: { upi_id: 'demoengineering@okaxis', amount: 297360, link: 'upi://pay?pa=demoengineering@okaxis&am=297360.00', qr: 'data:image/png;base64,iVBORw0KGgo=' },
  upi_missing: false, pdf: '/invoices/D-58/pdf', email: true,
  actions: { make: '/api/document/D-58/share', off: '/api/document/D-58/share' },
};
const WITH_LINK: ShareData = { ...NO_LINK, link: { url: URL, opens: 2, last_opened: '2 Nov 2026', made: '1 Nov 2026' },
                               body: BODY.replace('[link]', URL) };

function serve() {
  const fetch = vi.fn(async (_path: string, init?: RequestInit) => {
    const body = !init?.method || init.method === 'GET' ? NO_LINK : init.method === 'POST' ? WITH_LINK : NO_LINK;
    return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('sharing a document', () => {
  it('makes the private link only when WhatsApp is chosen, then offers the project\'s people with a phone', async () => {
    const fetch = serve();
    render(<ShareDialog url="/api/document/D-58/share" projectId="P-7" invoiceId="D-58" onClose={() => undefined} />);
    expect(await screen.findByRole('heading', { name: 'Share TF/INV/058/26-27', hidden: true })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(1);                                           // looking makes no link
    expect(screen.getByRole('img', { name: /UPI QR code to pay ₹2,97,360/, hidden: true })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'WhatsApp', hidden: true }));
    expect(fetch.mock.calls[1][1]?.method).toBe('POST');
    const karthik = await screen.findByRole('link', { name: 'Mr. Karthik', hidden: true });
    const text = decodeURIComponent(karthik.getAttribute('href')!.split('?text=')[1]);
    expect(karthik.getAttribute('href')).toMatch(/^https:\/\/wa\.me\/919876543210\?text=/);
    expect(text.startsWith('Dear Mr. Karthik,\nPlease find our invoice')).toBe(true);
    expect(text).toContain(URL);                                                          // the link took [link]'s place
    expect(screen.getByRole('link', { name: 'Someone else', hidden: true }).getAttribute('href')).toMatch(/^https:\/\/wa\.me\/\?text=Hello%2C/);
    expect(screen.getByText(/Accounts · \+91 91234 56789 · not on this document/)).toBeInTheDocument();
    expect(screen.getByText(/Opened 2 times, last on 2 Nov 2026/)).toBeInTheDocument();
  });

  it('copies the link, and turns it off', async () => {
    const fetch = serve();
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    render(<ShareDialog url="/api/document/D-58/share" projectId="P-7" invoiceId="D-58" onClose={() => undefined} />);
    await userEvent.click(await screen.findByRole('button', { name: 'Copy link', hidden: true }));
    expect(await screen.findByDisplayValue(URL)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Copy', hidden: true }));
    expect(writeText).toHaveBeenCalledWith(URL);
    await userEvent.click(screen.getByRole('button', { name: 'Turn the link off', hidden: true }));
    expect(fetch.mock.calls.at(-1)?.[1]?.method).toBe('DELETE');
    expect(screen.queryByDisplayValue(URL)).toBeNull();
  });

  it('offers no email outside a project, and no QR code without a UPI ID', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ ...NO_LINK, pay: null, upi_missing: true, email: false }),
                                                          { status: 200, headers: { 'Content-Type': 'application/json' } })));
    render(<ShareDialog url="/api/document/D-58/share" projectId={null} invoiceId="D-58" onClose={() => undefined} />);
    const dialog = (await screen.findByRole('link', { name: 'Download PDF', hidden: true })).closest('dialog')!;
    expect(within(dialog).queryByRole('button', { name: 'Email', hidden: true })).toBeNull();
    expect(within(dialog).queryByRole('region', { name: 'Pay by UPI', hidden: true })).toBeNull();
    expect(within(dialog).getByRole('link', { name: 'Download PDF', hidden: true })).toHaveAttribute('href', '/invoices/D-58/pdf?download=1');
  });

  it('builds wa.me links the way WhatsApp reads them', () => {
    expect(waLink('Dear Ravi,\nPay ₹4,500 & thanks', '919876543210')).toBe(
      'https://wa.me/919876543210?text=Dear%20Ravi%2C%0APay%20%E2%82%B94%2C500%20%26%20thanks');
  });
});
