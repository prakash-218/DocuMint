// Costing editor: items and their cost lines. The numbers come from the server
// (POST .../preview, the same costing.py that saves), so what's shown is what's saved.
(function () {
    var form = document.querySelector('[data-costing]');
    if (!form) return;
    var table = form.querySelector('.k-items');
    var status = form.querySelector('.k-status');
    var sheetInput = form.querySelector('[name="sheet_json"]');

    function currency() { return form.querySelector('[name="currency"]').value || 'INR'; }
    function money(v) {
        if (v === null || v === undefined || !isFinite(v)) return '—';
        try {
            return new Intl.NumberFormat(currency() === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency: currency() }).format(v);
        } catch (e) { return Number(v).toFixed(2); }
    }
    function plain(v) { return (v === null || v === undefined || !isFinite(v)) ? '' : String(Math.round(v * 100) / 100); }
    function val(scope, key) { var el = scope.querySelector('[data-k="' + key + '"]'); return el ? el.value : ''; }

    function collect() {
        var items = [];
        table.querySelectorAll('tbody.k-item').forEach(function (body) {
            var row = body.querySelector('.k-item-row');
            var lines = [];
            body.querySelectorAll('tr.k-line').forEach(function (tr) {
                lines.push({ description: val(tr, 'description'), make: val(tr, 'make'), qty: val(tr, 'qty'),
                             unit: val(tr, 'unit'), unit_cost: val(tr, 'unit_cost'), markup: val(tr, 'markup') });
            });
            items.push({ name: val(row, 'name'), description: val(row, 'description'), qty: val(row, 'qty'),
                         unit: val(row, 'unit'), cost_each: val(row, 'cost_each'), profit_percent: val(row, 'profit_percent'),
                         price_each: val(row, 'price_each'), lines: lines });
        });
        return { items: items };
    }

    function number(no) {
        table.querySelectorAll('tbody.k-item').forEach(function (body, i) {
            body.querySelector('.row-no').textContent = i + 1;
            var count = body.querySelectorAll('tr.k-line').length;
            body.querySelector('.k-line-count').textContent = count || '';
            var input = body.querySelector('.k-cost-input'), out = body.querySelector('.k-cost-out');
            input.hidden = count > 0;                    // with cost lines, the cost is their total
            out.hidden = count === 0;
        });
    }

    // The server skips blank items, so match its items to the rows that aren't blank
    function filledRows() {
        var rows = [];
        table.querySelectorAll('tbody.k-item').forEach(function (body) {
            var row = body.querySelector('.k-item-row');
            var filled = val(row, 'name').trim() || val(row, 'cost_each') || val(row, 'price_each') ||
                Array.prototype.some.call(body.querySelectorAll('tr.k-line'), function (tr) {
                    return val(tr, 'description').trim() || val(tr, 'unit_cost');
                });
            if (filled) rows.push(body);
        });
        return rows;
    }

    function show(result) {
        var rows = filledRows();
        result.items.forEach(function (it, i) {
            var body = rows[i];
            if (!body) return;
            body.classList.toggle('manual', !!it.manual_price);
            body.querySelector('[data-out="cost_each"]').textContent = money(it.cost_each);
            body.querySelector('[data-out="amount"]').textContent = money(it.amount);
            body.querySelector('[data-out="profit"]').textContent = money(it.profit);
            body.querySelector('[data-out="profit_on_cost"]').textContent = it.profit_on_cost === null ? '' : it.profit_on_cost + '%';
            body.querySelector('.k-price').placeholder = plain(it.price);
            body.querySelector('[data-k="profit_percent"]').placeholder = plain(result.profit_percent);
            var lineRows = Array.prototype.filter.call(body.querySelectorAll('tr.k-line'), function (tr) {
                return val(tr, 'description').trim() || val(tr, 'unit_cost');
            });
            it.lines.forEach(function (l, j) {
                if (lineRows[j]) lineRows[j].querySelector('[data-out="line_cost"]').textContent = money(l.cost);
            });
        });
        var t = result.totals;
        form.querySelectorAll('[data-total]').forEach(function (el) {
            var key = el.dataset.total, v = key === 'profit_percent' ? result.profit_percent : t[key];
            el.textContent = (key === 'profit_on_cost' || key === 'margin_of_price' || key === 'profit_percent')
                ? (v === null || v === undefined ? '—' : plain(v)) : money(v);
        });
        var left = form.querySelector('.k-left');
        if (left) left.classList.toggle('k-over', t.left !== undefined && t.left !== null && t.left < 0);
        var off = form.querySelector('.k-off');
        if (off) off.hidden = !t.off_target;
        status.textContent = '';
    }

    var timer = null, pending = null;
    function preview() {
        clearTimeout(timer);
        timer = setTimeout(function () {
            var data = new FormData(form);
            data.set('sheet_json', JSON.stringify(collect()));
            if (pending) pending.abort();
            pending = new AbortController();
            fetch(form.dataset.preview, { method: 'POST', body: data, credentials: 'same-origin', signal: pending.signal })
                .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                .then(show)
                .catch(function (e) { if (e.name !== 'AbortError') status.textContent = "Couldn't work out the numbers; they're updated when you save."; });
        }, 250);
    }

    function setMode() {
        var checked = form.querySelector('[name="mode"]:checked');
        form.dataset.mode = checked ? checked.value : 'build';
        form.querySelectorAll('.k-modes label').forEach(function (l) { l.classList.toggle('active', l.querySelector('input').checked); });
    }

    function fromTemplate(id, selector) {
        var tpl = document.getElementById(id);
        return tpl.content.querySelector(selector).cloneNode(true);
    }
    function addLine(body) {
        var tr = fromTemplate('k-line-template', 'tr');
        body.querySelector('.k-lines tbody').appendChild(tr);
        body.querySelector('.k-lines-row').hidden = false;
        body.querySelector('.k-toggle-lines').setAttribute('aria-expanded', 'true');
        if (window.lucide) window.lucide.createIcons();
        tr.querySelector('input').focus();
    }

    table.addEventListener('click', function (e) {
        var btn = e.target.closest('button');
        if (!btn) return;
        var body = btn.closest('tbody.k-item');
        if (btn.classList.contains('k-remove-item')) {
            body.remove();
        } else if (btn.classList.contains('k-remove-line')) {
            btn.closest('tr.k-line').remove();
        } else if (btn.classList.contains('k-add-line')) {
            addLine(body);
            number();
            return;
        } else if (btn.classList.contains('k-toggle-lines')) {
            var row = body.querySelector('.k-lines-row');
            if (!body.querySelector('tr.k-line')) { addLine(body); number(); return; }
            row.hidden = !row.hidden;
            btn.setAttribute('aria-expanded', String(!row.hidden));
            return;
        } else {
            return;
        }
        number();
        preview();
    });

    form.querySelector('.k-add-item').addEventListener('click', function () {
        var body = fromTemplate('k-item-template', 'tbody');
        table.appendChild(body);
        if (window.lucide) window.lucide.createIcons();
        number();
        body.querySelector('.k-name').focus();
    });

    form.addEventListener('input', function (e) {
        if (e.target.name === 'sheet_json' || e.target.name === 'notes' || e.target.name === 'template_id') return;
        if (e.target.classList.contains('k-desc')) { e.target.style.height = 'auto'; e.target.style.height = e.target.scrollHeight + 'px'; }
        preview();
    });
    form.addEventListener('change', function (e) {
        if (e.target.name === 'mode') setMode();
        if (e.target.name === 'mode' || e.target.name === 'round_to' || e.target.name === 'currency') preview();
    });
    form.addEventListener('submit', function () { sheetInput.value = JSON.stringify(collect()); });

    if (!table.querySelector('tbody.k-item')) form.querySelector('.k-add-item').click();
    form.querySelectorAll('.k-desc').forEach(function (t) { if (t.value) t.style.height = t.scrollHeight + 'px'; });
    setMode();
    number();
})();
