// Document editor: add / remove lines, live amounts and totals, GST preview.
// The preview only handles arithmetic on this.<field>, SUM(section.field) and
// other fields' names; anything else shows "—" and is worked out on save.
(function () {
    var form = document.querySelector('[data-editor]');
    if (!form) return;

    var currency = document.getElementById('currency');
    function money(v) {
        if (!isFinite(v)) return '—';
        var code = (currency && currency.value) || form.dataset.currency || 'INR';
        try {
            return new Intl.NumberFormat(code === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency: code }).format(v);
        } catch (e) {
            return v.toFixed(2);
        }
    }

    function evaluate(expr) {
        if (!/^[\d.\s+\-*/()eE]+$/.test(expr)) return NaN;
        try { return Function('"use strict"; return (' + expr + ');')(); } catch (e) { return NaN; }
    }

    function rowValues(tr) {
        var vals = {};
        tr.querySelectorAll('[data-field]').forEach(function (el) {
            var v = el.tagName === 'OUTPUT' ? parseFloat(el.dataset.value) : parseFloat(el.value);
            vals[el.dataset.field] = isNaN(v) ? 0 : v;
        });
        return vals;
    }

    function recalc() {
        var sums = {};
        form.querySelectorAll('.items-card').forEach(function (card) {
            var section = card.dataset.sectionName;
            card.querySelectorAll('tbody tr').forEach(function (tr, i) {
                var no = tr.querySelector('.row-no');
                if (no) no.textContent = i + 1;
                tr.querySelectorAll('output[data-formula]').forEach(function (out) {
                    var vals = rowValues(tr);
                    var expr = out.dataset.formula.replace(/this\.(\w+)/g, function (m, k) {
                        return k in vals ? '(' + vals[k] + ')' : 'NaN';
                    });
                    var v = evaluate(expr);
                    out.dataset.value = isFinite(v) ? v : '';
                    out.textContent = isFinite(v) ? (out.dataset.money === '1' ? money(v) : +v.toFixed(4)) : '—';
                });
                var vals = rowValues(tr);
                Object.keys(vals).forEach(function (k) {
                    sums[section + '.' + k] = (sums[section + '.' + k] || 0) + vals[k];
                });
            });
        });

        var named = {};
        form.querySelectorAll('[data-normal-field]').forEach(function (el) {
            named[el.dataset.normalField] = parseFloat(el.value) || 0;
        });
        var total = NaN;
        form.querySelectorAll('output[data-total-formula]').forEach(function (out) {
            var expr = out.dataset.totalFormula
                .replace(/SUM\(\s*(\w+)\.(\w+)\s*\)/gi, function (m, s, f) { return '(' + (sums[s.toLowerCase() + '.' + f] || 0) + ')'; })
                .replace(/\b([A-Za-z_]\w*)\b/g, function (m, k) { return k in named ? '(' + named[k] + ')' : m; });
            var v = evaluate(expr);
            if (isFinite(v)) named[out.dataset.field] = v;
            out.textContent = money(v);
            total = v;
        });

        var mode = document.getElementById('tax_mode');
        var rate = parseFloat((document.getElementById('tax_rate') || {}).value) || 0;
        var taxed = mode && (mode.value === 'cgst_sgst' || mode.value === 'igst');
        var tax = taxed && isFinite(total) ? total * rate / 100 : 0;
        var hasTotals = !!form.querySelector('output[data-total-formula]');
        form.querySelectorAll('.tax-line').forEach(function (el) { el.hidden = !taxed; });
        form.querySelectorAll('.editor-summary .grand').forEach(function (el) { el.hidden = !taxed && hasTotals; });
        var taxLabel = form.querySelector('dt.tax-line');
        if (taxLabel) taxLabel.textContent = mode && mode.value === 'igst' ? 'IGST ' + rate + '%' : 'GST ' + rate + '%';
        var taxOut = document.getElementById('sum_tax');
        var grand = document.getElementById('sum_grand');
        if (taxOut) taxOut.textContent = money(tax);
        if (grand) grand.textContent = money(isFinite(total) ? total + tax : NaN);
    }

    function grow(el) {
        el.style.height = 'auto';
        el.style.height = el.scrollHeight + 'px';
    }

    form.addEventListener('click', function (e) {
        var add = e.target.closest('.add-row');
        if (add) {
            var card = add.closest('.items-card');
            var tbody = card.querySelector('tbody');
            var max = 0;
            tbody.querySelectorAll('tr[data-row]').forEach(function (tr) { max = Math.max(max, parseInt(tr.dataset.row, 10) || 0); });
            var html = card.querySelector('.row-template').innerHTML.replace(/__ROW__/g, String(max + 1));
            tbody.insertAdjacentHTML('beforeend', html);
            if (window.lucide) window.lucide.createIcons();
            var first = tbody.lastElementChild.querySelector('textarea, input:not([type=hidden])');
            if (first) first.focus();
            recalc();
            return;
        }
        var remove = e.target.closest('.remove-row');
        if (remove) {
            var tr = remove.closest('tr');
            if (tr.parentElement.children.length > 1) {
                tr.remove();
            } else {
                tr.querySelectorAll('input:not([type=hidden]), textarea').forEach(function (el) {
                    if (el.type === 'checkbox') el.checked = false; else el.value = '';
                });
            }
            recalc();
        }
    });
    form.addEventListener('input', function (e) {
        if (e.target.classList.contains('line-text')) grow(e.target);
        recalc();
    });
    form.addEventListener('change', recalc);
    form.querySelectorAll('.line-text').forEach(grow);

    // GST: show the rate only when taxed, explain the split, follow the customer's state
    var mode = document.getElementById('tax_mode');
    var rateGroup = document.getElementById('tax_rate_group');
    var rateInput = document.getElementById('tax_rate');
    var hint = document.getElementById('tax_split_hint');
    var hintsEl = document.getElementById('tax_hints');
    var hints = hintsEl ? JSON.parse(hintsEl.textContent || '{}') : {};
    function refreshTax() {
        if (!mode) return;
        var taxed = mode.value === 'cgst_sgst' || mode.value === 'igst';
        if (rateGroup) rateGroup.style.display = taxed ? '' : 'none';
        var r = parseFloat(rateInput && rateInput.value) || 0;
        if (hint) hint.textContent = mode.value === 'cgst_sgst' ? 'CGST ' + r / 2 + '% + SGST ' + r / 2 + '%' : '';
    }
    var customer = document.getElementById('customer_id');
    if (customer && customer.tagName === 'SELECT') {
        customer.addEventListener('change', function () {
            if (hints[customer.value] && mode) { mode.value = hints[customer.value]; refreshTax(); recalc(); }
        });
    }
    if (mode) mode.addEventListener('change', refreshTax);
    if (rateInput) rateInput.addEventListener('input', refreshTax);
    refreshTax();
    recalc();
})();
