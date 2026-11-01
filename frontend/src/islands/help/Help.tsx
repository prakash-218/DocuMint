import type { ReactNode } from 'react';
import { useBoot } from '../../app/Layout';
import { PageHeader } from '../../app/PageHeader';

// How the app works, by area (/settings/help): the notes the screens leave out, so they show only facts about the
// work. A section shows when they have any of its permissions (me.permissions), so Sales don't read about costings.

interface Section { id: string; title: string; needs: string[]; body: ReactNode }

const DOCS = ['quotes.read', 'proformas.read', 'invoices.read', 'purchases.read'];
const WRITE_DOCS = ['quotes.write', 'proformas.write', 'invoices.write', 'purchases.write'];

const SECTIONS: Section[] = [
  {
    id: 'projects', title: 'Projects', needs: ['projects.read'], body: (
      <>
        <p>A project is one customer job. Its stage (Quoted, Accepted, Advance, Invoiced, Paid) is worked out from its documents.</p>
        <ul>
          <li>The documents come in order: the quotation first; a proforma for the advance once the quotation is accepted
            and an advance is asked for; then the tax invoice on delivery, with the advance taken off it.</li>
          <li>Start with a quotation, or upload one made earlier under Files.</li>
          <li>An email whose subject has the project's code (PRJ-012) or one of its document numbers goes to the project by itself.</li>
          <li>To say what a file is or give its number (a PO or drawing no.), open its tag. Files dropped on a customer's
            page go in no project; move them into one from their tag.</li>
          <li>Projects with nothing left to do can be marked completed, or seen in the list.</li>
        </ul>
      </>
    ),
  },
  {
    id: 'quotations', title: 'Quotations', needs: ['quotes.read'], body: (
      <ul>
        <li>Check a draft, then finalize it or mark it as sent. It can't be edited afterwards; changes go into a revision,
          and the newest revision is the one to send or convert.</li>
        <li>With no answer for 14 days, a quotation needs a follow-up.</li>
        <li>Once it's accepted, raise a proforma for the advance or invoice it in full. In the Sales role, the office raises
          the proforma and the invoice.</li>
        <li>If it's declined, revise it to send a new offer.</li>
        <li>"Invoiced X of Y" compares what's been invoiced with the quotation, both before GST.</li>
      </ul>
    ),
  },
  {
    id: 'changing', title: 'Revise, correct or undo', needs: WRITE_DOCS, body: (
      <dl className="help-terms">
        <dt>Correct</dt>
        <dd>Fixes a mistake, such as a wrong PO number, date, rate or spelling. It keeps its number and its payments, and the
          correction replaces what was sent. It's recorded in the audit log. If the total changes, paid or pending follows
          the payments recorded. Download the PDF again afterwards and send the corrected one.</dd>
        <dt>Revise</dt>
        <dd>A new version, with R1, R2… after the number, for a changed offer: other prices, items or terms. The old one
          stays as it was sent, marked revised. Advances received move to the revision.</dd>
        <dt>Back to draft</dt>
        <dd>Undoes "Mark as sent" or "Finalize" done by mistake. It keeps its number; edit it and send it again.</dd>
      </dl>
    ),
  },
  {
    id: 'advances', title: 'Proformas and advances', needs: ['proformas.read'], body: (
      <ul>
        <li>Money received against a proforma is an advance. When the proforma is converted, the advance moves to the tax
          invoice and comes off what's due.</li>
        <li>Home shows advances asked for on proformas; they count as received once paid.</li>
        <li>A customer's statement leaves out proformas until they're paid. "Paid ahead" is an advance not on an invoice yet.</li>
      </ul>
    ),
  },
  {
    id: 'invoices', title: 'Invoices and payments', needs: ['invoices.read'], body: (
      <ul>
        <li>Payment terms are the days after the invoice date a customer pays (0 is on receipt): your usual ones in the
          Business profile, or a customer's own on their page. They decide when an invoice is overdue and aren't printed.</li>
        <li>With a UPI ID in the Business profile, proformas and invoices with something due print a "Scan to pay" QR code
          for that amount. The share dialog and the link's page show it too.</li>
        <li>Invoices made with an export template print as Export Invoice, under LUT, with the shipping details and the packing list.</li>
        <li>Payments lists every payment received, with its bank reference. Its CSV is for the accountant; a list's CSV has
          a row for each document with its taxable value and GST.</li>
      </ul>
    ),
  },
  {
    id: 'notes', title: 'Credit and debit notes', needs: ['invoices.read'], body: (
      <ul>
        <li>A credit note lowers what an invoice is owed: goods returned, a price reduced after the invoice, or too much
          billed. A debit note raises it, for more charged after the invoice.</li>
        <li>Make one from a sent invoice's page. It starts with the invoice's lines, customer and GST; change the lines to
          what's credited or charged, and give the reason.</li>
        <li>Notes have their own numbers (CN/001/26-27 and DN/001/26-27 to start), set in the Business profile, and are
          listed under Invoices in their own tabs.</li>
        <li>An issued note counts on its invoice: on what's due, and the invoice is paid once nothing is left. A draft or
          cancelled note doesn't count. A credit note can't be more than is left on its invoice.</li>
        <li>When the invoice was paid already, a credit note leaves money to refund. Record the refund on the credit note.</li>
        <li>Correct changes the invoice itself; a note leaves the invoice as it was sent and records the change. An invoice
          with notes issued against it can't go back to draft or be deleted: cancel its notes first.</li>
      </ul>
    ),
  },
  {
    id: 'purchases', title: 'Purchase orders', needs: ['purchases.read'], body: (
      <ul>
        <li>A purchase order goes to one of your suppliers, for one of your projects. GST is worked out from the supplier's
          GSTIN, as on an invoice.</li>
        <li>Send it, then mark it confirmed when they confirm it. Record each delivery as it arrives; the order is received
          once everything has come. Taking a delivery off puts it back to confirmed. Use "Mark it all received" when you
          don't record line by line.</li>
        <li>When recording a delivery, each line starts at what's still to come; enter 0 for a line that didn't come.</li>
        <li>From a costing, "Make a purchase order" takes the cost lines you tick, from one supplier. Each comes with its
          make, its quantity for all the items, its unit and its cost as the rate; you pick the supplier and check it
          before it's made. Unsaved changes to the costing aren't included.</li>
      </ul>
    ),
  },
  {
    id: 'costing', title: 'Costing and rates', needs: ['costings.read'], body: (
      <>
        <p>Only owners and admins see costings and rates.</p>
        <dl className="help-terms">
          <dt>Build up from costs</dt>
          <dd>Each item's price is its cost plus the profit; an item can have its own %. Type a price to set one yourself,
            and clear it to work it out again.</dd>
          <dt>Work back from a total</dt>
          <dd>The known total is shared over the items by their cost, and the cost budget is what's left after your profit.
            Type a price to fix one item's share.</dd>
        </dl>
        <ul>
          <li>"Costing for" becomes the quotation's subject.</li>
          <li>An item's cost is the total of its cost lines. Cost lines stay in the costing; the quotation gets the items and prices.</li>
          <li>Shared costs, such as design, freight, a reference station or an allowance for changes, are spread over the
            items, so their prices carry them.</li>
          <li>Costs stay in your main currency; prices, profit and the quotation are in the quote's currency at the exchange rate.</li>
          <li>"Save and make the quote" makes a draft quotation with the items and prices. Once the quotation has gone out it
            stays as it is: to requote, start a new version, which copies what's saved.</li>
          <li>Copying from a costing brings each item with its cost lines; shared costs stay behind. An Excel file is read to
            pick the rows from and isn't kept.</li>
          <li>Rates are your usual unit costs: a cost line offers them as you type. "From your costings" lists cost lines
            you've used that aren't in the list yet, with the rate they had last.</li>
        </ul>
      </>
    ),
  },
  {
    id: 'editor', title: 'Making a document', needs: WRITE_DOCS, body: (
      <ul>
        <li>A discount is an amount (5000) or a percent (10%), taken off before tax, on a line or on the total.</li>
        <li>Tax follows the GSTINs: the same state is CGST + SGST, another state IGST, and an export LUT. With your GSTIN in
          the Business profile, new documents pick it by themselves and say why.</li>
        <li>Notes print below the items. On a purchase order, Deliver to is for when the goods go somewhere other than the
          address on top.</li>
      </ul>
    ),
  },
  {
    id: 'templates', title: 'Templates', needs: ['templates.write'], body: (
      <ul>
        <li>Templates set the columns and formulas of your documents. The ready-made ones (quotation, export quotation,
          proforma, tax and export invoice) are added from the Business profile; existing templates are kept.</li>
        <li>A formula on a line looks like <code>this.rate * this.qty</code>; a column total like <code>SUM(items.amount)</code>.</li>
        <li>Cost break-up lines explain an item's price and are never added to the total.</li>
        <li>New documents of the ticked types offer the template; with none ticked, every type does. If nothing is set, the
          types are guessed from its name.</li>
        <li>The main document page always prints first; other pages print with it or as a separate PDF. Tick "Total at end"
          for weights. Copies are one per line, up to 5.</li>
        <li>An archived template stays on the documents made with it, but can't be picked for new ones.</li>
      </ul>
    ),
  },
  {
    id: 'sharing', title: 'Email and sharing', needs: DOCS, body: (
      <ul>
        <li>You pick who gets each email. Who usually gets what is set on the project page, under People.</li>
        <li>Anyone with a document's share link can open it and its PDF without signing in. Turn the link off to stop that.</li>
        <li>On WhatsApp the message starts "Dear …," with the name of whoever you send it to. Contacts with a phone number are
          offered; otherwise pick someone in WhatsApp.</li>
      </ul>
    ),
  },
  {
    id: 'customers', title: 'Customers and suppliers', needs: ['customers.read'], body: (
      <ul>
        <li>A company can be a customer, a supplier or both. A site (a plant, branch, division or sister company billed
          separately) is whatever its company is, and uses its company's contacts. A site's name defaults to its city.</li>
        <li>A GSTIN's state decides CGST + SGST or IGST. On a site, add only its own email domains.</li>
        <li>A customer can sign in to the customer portal with the email and password you give them, to see and download
          their invoices.</li>
      </ul>
    ),
  },
  {
    id: 'business', title: 'Business profile', needs: ['business.write'], body: (
      <ul>
        <li>Numbering uses <code>{'{num}'}</code> or <code>{'{num:03}'}</code> for zero-padding, <code>{'{fy}'}</code> for the
          financial year (26-27) and <code>{'{yyyy}'}</code>. Each type restarts at 1 every financial year; set "next" to
          continue an existing series. Export invoices continue the tax-invoice series unless they have their own.</li>
        <li>Team addresses are personal addresses your people also write from. They count as yours, so they're never
          suggested as a customer's contact.</li>
        <li>The main currency is the one Home's totals are in. SWIFT is for payments from abroad; the IEC code prints on
          export invoices.</li>
        <li>Custom fields about your organization (an MSME or Udyam no., CIN) print under your address. Fields on every
          customer (a vendor code, plant, PAN) print in the consignee block when ticked.</li>
        <li>Quotation defaults start every new quotation and can be changed on each one; empty uses DocuMint's own.</li>
        <li>Logos, the stamp and the signature are PNG or JPEG up to 300 KB; a transparent background looks best. The
          invoice logo is a smaller one, printed beside the name. "Signed by" prints under the signature on quotations.</li>
      </ul>
    ),
  },
  {
    id: 'team', title: 'Team and roles', needs: ['team.manage'], body: (
      <>
        <ul>
          <li>Only people you invite can get in. Any address works, Gmail too: they open the link, set a password and
            they're in, with the role you chose.</li>
          <li>An invite link works once, for 7 days, and only for that address; a password reset link works for 2 hours.
            Neither is shown again: send it again for a new one. Make a password link when someone forgot theirs and
            email doesn't reach them.</li>
          <li>Changes to a role apply to its people at once. Make a role from scratch, or copy a built-in one and change it.</li>
        </ul>
        <dl className="help-terms">
          <dt>Owner</dt><dd>Everything, including the name and address and who the owners are.</dd>
          <dt>Admin</dt><dd>Everything but the organization's name and address, and making or changing owners.</dd>
          <dt>Member</dt><dd>Every document (purchase orders too), payments, projects and files, reading customers and the
            mailbox, and sending email.</dd>
          <dt>Sales</dt><dd>Projects and their files, quotations and customers; nothing about money beyond what's quoted.</dd>
          <dt>Viewer</dt><dd>Reads documents, projects, files, customers and templates, and changes nothing.</dd>
        </dl>
      </>
    ),
  },
  {
    id: 'organization', title: 'Name, address and audit log', needs: ['organization.write', 'audit.read'], body: (
      <ul>
        <li>A change to the name or address shows on documents made from then on. The domain can't be changed.</li>
        <li>The audit log shows who changed what, newest first.</li>
      </ul>
    ),
  },
];

export default function Help() {
  const have = new Set(useBoot()?.me.permissions ?? []);
  const shown = SECTIONS.filter((s) => s.needs.some((p) => have.has(p)));
  return (
    <>
      <PageHeader title="Help" crumbs={[{ label: 'Settings', href: '/settings/' }, { label: 'Help' }]} />
      <div className="ui">
        <div className="help-grid">
          <nav className="help-toc" aria-label="Help topics">
            <ul>{shown.map((s) => <li key={s.id}><a href={`#${s.id}`}>{s.title}</a></li>)}</ul>
          </nav>
          <div className="help-sections">
            {shown.map((s) => (
              <section className="card help-section" key={s.id} id={s.id} aria-labelledby={`${s.id}-h`}>
                <div className="card-h"><h2 id={`${s.id}-h`}>{s.title}</h2></div>
                <div className="card-b">{s.body}</div>
              </section>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
