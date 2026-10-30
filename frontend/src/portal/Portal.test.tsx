import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { isPortalScreen, Portal, type PortalBoot } from './Portal';

const BOOT: PortalBoot = { customer: { name: 'Gear Cutters Ltd', email: 'accounts@gearcutters.example' },
                           links: { dashboard: '/customer/', logout: '/customer/logout' }, flashes: [{ category: 'success', text: 'Login successful' }] };
const DOC = '/customer/invoices/0b4c1d2e-3f40-4a51-8b62-7c83d94ea5f6';

function serve(body: unknown) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify(body), { status: 200 }));
}

afterEach(() => {
  vi.restoreAllMocks();
  window.history.pushState({}, '', '/');
});

describe('the customer portal', () => {
  it('knows its own screens', () => {
    expect(isPortalScreen('/customer/')).toBe(true);
    expect(isPortalScreen(DOC)).toBe(true);
    expect(isPortalScreen(`${DOC}/pdf`)).toBe(false);                     // the PDF downloads
    expect(isPortalScreen('/customer/login')).toBe(false);
  });

  it('lists the documents with what is owed, and the message the last page left', async () => {
    window.history.pushState({}, '', '/customer/');
    const fetched = serve({ title: 'My documents', stats: { outstanding: '₹45,000.00', overdue: 1, paid: '₹10,000.00' },
                            rows: [{ id: 'D-1', url: DOC, pdf: `${DOC}/pdf`, number: 'GC/INV/007', kind: 'Tax Invoice', date: 'Oct 2, 2026', due: 'Nov 1, 2026',
                                     status: { text: 'Overdue', tone: 'danger' }, total: '₹45,000.00', balance: '₹45,000.00' }],
                            page: { page: 1, pages: 1, first: 1, last: 1, total: 1, numbers: [1], noun: '' } });
    render(<Portal boot={BOOT} />);
    expect(await screen.findByText('GC/INV/007')).toHaveAttribute('href', DOC);
    expect(fetched.mock.calls[0][0]).toBe('/customer/api/documents');
    expect(screen.getByText('Overdue')).toHaveClass('badge-danger');
    expect(screen.getByText('Login successful')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download GC/INV/007 as a PDF' })).toHaveAttribute('target', '_blank');
    expect(screen.getByRole('button', { name: 'Log out' }).closest('form')).toHaveAttribute('action', '/customer/logout');
  });

  it('shows a document as the server draws it, with its PDF', async () => {
    window.history.pushState({}, '', DOC);
    serve({ title: 'GC/INV/007', from: 'Spline Works', back: '/customer/', pdf: `${DOC}/pdf`,
            document_html: '<article class="card invoice-doc"><p>Spline gauge × 2</p></article>', summary_html: '<div class="card">Due ₹45,000.00</div>' });
    render(<Portal boot={BOOT} />);
    expect(await screen.findByText('Spline gauge × 2')).toBeInTheDocument();
    expect(screen.getByText('From Spline Works')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download PDF' })).toHaveAttribute('href', `${DOC}/pdf`);
    expect(document.title).toBe('GC/INV/007 · DocuMint');
  });
});
