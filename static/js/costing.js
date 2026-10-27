// Costing editor: items and their cost lines, and the shared costs spread over them. The numbers
// come from the server (POST .../preview, the same costing.py that saves), so what's shown is
// what's saved. Items carry a key, which is how shared costs name the items they're spread over
// and how the worked-out numbers find their row. window.KCosting lets costing-import.js add rows.
(function () {
    var form = document.querySelector('[data-costing]');
    if (!form) return;
    var table = form.querySelector('.k-items');
    var shared = form.querySelector('.k-shared');
    var status = form.querySelector('.k-status');
    var sheetInput = form.querySelector('[name="sheet_json"]');
    var base = form.dataset.base || 'INR';
    var rates = [];
    try { rates = JSON.parse(document.getElementById('k-rates-data').textContent) || []; } catch (e) { rates = []; }

    function currency() { return form.querySelector('[name="currency"]').value || base; }
    function money(v, cur) {
        cur = cur || currency();
        if (v === null || v === undefined || !isFinite(v)) return '—';
        try {
            return new Intl.NumberFormat(cur === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency: cur }).format(v);
        } catch (e) { return Number(v).toFixed(2); }
    }
    function plain(v) { return (v === null || v === undefined || !isFinite(v)) ? '' : String(Math.round(v * 100) / 100); }
    function field(scope, key) { return scope.querySelector('[data-k="' + key + '"]'); }
    function val(scope, key) { var el = field(scope, key); return el ? el.value : ''; }
    function setVal(scope, key, v) {
        var el = field(scope, key);
        if (el && v !== null && v !== undefined && v !== '') el.value = v;
    }
    function newKey() {
        var bytes = new Uint8Array(4);
        (window.crypto || window.msCrypto).getRandomValues(bytes);
        return 'i' + Array.prototype.map.call(bytes, function (b) { return ('0' + b.toString(16)).slice(-2); }).join('');
    }
    function itemBodies() { return Array.prototype.slice.call(table.querySelectorAll('tbody.k-item')); }
    function sharedRows() { return Array.prototype.slice.call(shared.querySelectorAll('tr.k-share')); }
    function chosen(tr) { try { return JSON.parse(tr.dataset.items || '[]'); } catch (e) { return []; } }

    function collect() {
        var items = itemBodies().map(function (body) {
            var row = body.querySelector('.k-item-row');
            var lines = Array.prototype.map.call(body.querySelectorAll('tr.k-line'), function (tr) {
                return { description: val(tr, 'description'), make: val(tr, 'make'), qty: val(tr, 'qty'),
                         unit: val(tr, 'unit'), unit_cost: val(tr, 'unit_cost'), markup: val(tr, 'markup') };
            });
            return { key: body.dataset.key, name: val(row, 'name'), description: val(row, 'description'), qty: val(row, 'qty'),
                     unit: val(row, 'unit'), cost_each: val(row, 'cost_each'), profit_percent: val(row, 'profit_percent'),
                     price_each: val(row, 'price_each'), lines: lines };
        });
        var shares = sharedRows().map(function (tr) {
            return { description: val(tr, 'description'), kind: val(tr, 'kind'), qty: val(tr, 'qty'), unit_cost: val(tr, 'unit_cost'),
                     markup: val(tr, 'markup'), percent: val(tr, 'percent'), spread: val(tr, 'spread'), items: chosen(tr) };
        });
        var rate = form.querySelector('[name="exchange_rate"]');
        return { items: items, shared: shares, exchange_rate: rate ? rate.value : '' };
    }

    // Renumber the items, show typed cost or the lines' total, and keep the shared costs' item pickers current
    function number() {
        itemBodies().forEach(function (body, i) {
            if (!body.dataset.key) body.dataset.key = newKey();
            body.querySelector('.row-no').textContent = i + 1;
            var count = body.querySelectorAll('tr.k-line').length;
            body.querySelector('.k-line-count').textContent = count || '';
            var input = body.querySelector('.k-cost-input'), out = body.querySelector('.k-cost-out');
            input.hidden = count > 0;                    // with cost lines, the cost is their total
            out.hidden = count === 0;
        });
        shared.hidden = !shared.querySelector('tr.k-share');
        sharedRows().forEach(pickers);
    }

    function pickers(tr) {
        var bodies = itemBodies(), keys = bodies.map(function (b) { return b.dataset.key; });
        var picked = chosen(tr).filter(function (k) { return keys.indexOf(k) >= 0; });   // removed items drop out
        tr.dataset.items = JSON.stringify(picked);
        var box = tr.querySelector('.k-over-items');
        box.innerHTML = '';
        bodies.forEach(function (body, i) {
            var label = document.createElement('label');
            label.className = 'menu-check';
            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = body.dataset.key;
            cb.checked = picked.indexOf(body.dataset.key) >= 0;
            var span = document.createElement('span');
            span.textContent = (i + 1) + '. ' + (val(body.querySelector('.k-item-row'), 'name').trim() || 'Item ' + (i + 1));
            label.appendChild(cb);
            label.appendChild(span);
            box.appendChild(label);
        });
        var nos = picked.map(function (k) { return keys.indexOf(k) + 1; }).sort(function (a, b) { return a - b; });
        tr.querySelector('.k-over-label').textContent = !nos.length ? 'All items'
            : nos.length <= 3 ? (nos.length === 1 ? 'Item ' : 'Items ') + nos.join(', ') : nos.length + ' items';
    }

    function filledLine(tr) { return val(tr, 'description').trim() || val(tr, 'unit_cost'); }
    function filledShare(tr) { return val(tr, 'description').trim() || val(tr, 'unit_cost') || val(tr, 'percent'); }

    function show(result) {
        var byKey = {};
        itemBodies().forEach(function (body) { byKey[body.dataset.key] = body; });
        var cur = result.currency;
        result.items.forEach(function (it) {
            var body = byKey[it.key];
            if (!body) return;
            body.classList.toggle('manual', !!it.manual_price);
            body.querySelector('[data-out="own_cost_each"]').textContent = money(it.own_cost_each, base);
            var sub = body.querySelector('[data-out="shared_each"]');
            sub.hidden = !it.shared_each;
            sub.textContent = it.shared_each ? '+ ' + money(it.shared_each, base) + ' shared' : '';
            body.querySelector('[data-out="amount"]').textContent = money(it.amount, cur);
            body.querySelector('[data-out="profit"]').textContent = money(it.profit, cur);
            body.querySelector('[data-out="profit_on_cost"]').textContent = it.profit_on_cost === null ? '' : it.profit_on_cost + '%';
            body.querySelector('.k-price').placeholder = plain(it.price);
            field(body, 'profit_percent').placeholder = plain(result.profit_percent);
            var lineRows = Array.prototype.filter.call(body.querySelectorAll('tr.k-line'), filledLine);
            it.lines.forEach(function (l, j) {
                if (lineRows[j]) lineRows[j].querySelector('[data-out="line_cost"]').textContent = money(l.cost, base);
            });
        });
        var shareRows = sharedRows().filter(filledShare);
        result.shared.forEach(function (s, i) {
            if (shareRows[i]) shareRows[i].querySelector('[data-out="shared_amount"]').textContent = money(s.amount, base);
        });
        var t = result.totals;
        form.querySelectorAll('[data-total]').forEach(function (el) {
            var key = el.dataset.total, v = key === 'profit_percent' ? result.profit_percent : t[key];
            el.textContent = (key === 'profit_on_cost' || key === 'margin_of_price' || key === 'profit_percent')
                ? (v === null || v === undefined ? '—' : plain(v)) : money(v, el.dataset.in === 'base' ? base : cur);
        });
        form.querySelectorAll('.k-shared-only').forEach(function (el) { el.hidden = !t.shared; });
        var left = form.querySelector('.k-left');
        if (left) left.classList.toggle('k-over', t.left !== undefined && t.left !== null && t.left < 0);
        var off = form.querySelector('.k-off');
        if (off) off.hidden = !t.off_target;
        form.querySelector('.k-needs-rate').hidden = !result.needs_rate;
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
    function setCurrency() {
        form.dataset.foreign = String(currency() !== base);
        form.querySelectorAll('[data-cur-label]').forEach(function (el) { el.textContent = currency(); });
    }

    function fromTemplate(id, selector) {
        return document.getElementById(id).content.querySelector(selector).cloneNode(true);
    }
    function icons() { if (window.lucide) window.lucide.createIcons(); }

    function addLine(body, data) {
        var tr = fromTemplate('k-line-template', 'tr');
        if (data) ['description', 'make', 'qty', 'unit', 'unit_cost', 'markup'].forEach(function (k) { setVal(tr, k, data[k]); });
        body.querySelector('.k-lines tbody').appendChild(tr);
        body.querySelector('.k-lines-row').hidden = false;
        body.querySelector('.k-toggle-lines').setAttribute('aria-expanded', 'true');
        return tr;
    }
    function addItem(data) {
        var body = fromTemplate('k-item-template', 'tbody');
        body.dataset.key = newKey();
        var row = body.querySelector('.k-item-row');
        if (data) {
            ['name', 'description', 'qty', 'unit', 'profit_percent', 'price_each'].forEach(function (k) { setVal(row, k, data[k]); });
            if (!(data.lines && data.lines.length)) setVal(row, 'cost_each', data.cost_each);
            (data.lines || []).forEach(function (l) { addLine(body, l); });
            if (data.price_each !== null && data.price_each !== undefined && data.price_each !== '') body.classList.add('manual');
        }
        table.appendChild(body);
        return body;
    }
    // Rows added from elsewhere (an earlier costing, a spreadsheet): items, or cost lines of one item
    function isBlank(body) {
        var row = body.querySelector('.k-item-row');
        return !body.querySelector('tr.k-line') && ['name', 'description', 'qty', 'unit', 'cost_each', 'price_each', 'profit_percent']
            .every(function (k) { return !val(row, k).trim(); });
    }
    function addItems(list) {
        if (list.length) itemBodies().filter(isBlank).forEach(function (b) { b.remove(); });   // the empty starter row
        var added = list.map(addItem);
        icons(); number(); autosize(); preview();
        return added;
    }
    function addLinesTo(body, lines) {
        lines.forEach(function (l) { addLine(body, l); });
        icons(); number(); preview();
    }

    // A rate picked from the list fills the line's empty fields (description "MS plate — Tata" sets the make too)
    function applyRate(input) {
        var scope = input.closest('tr');
        var text = input.value.trim().toLowerCase();
        if (!text) return;
        var hit = null;
        rates.some(function (r) {
            var full = (r.description + (r.make ? ' — ' + r.make : '')).toLowerCase();
            if (full === text) { hit = r; return true; }
            if (!hit && r.description.toLowerCase() === text) hit = r;
            return false;
        });
        if (!hit) return;
        input.value = hit.description;
        var fill = { make: hit.make, unit: hit.unit, unit_cost: hit.unit_cost, markup: hit.markup };
        Object.keys(fill).forEach(function (k) {
            var el = field(scope, k);
            if (el && !el.value && fill[k] !== null && fill[k] !== undefined && fill[k] !== '') el.value = fill[k];
        });
    }

    form.addEventListener('click', function (e) {
        var btn = e.target.closest('button');
        if (!btn) return;
        var body = btn.closest('tbody.k-item');
        if (btn.classList.contains('k-remove-item')) {
            body.remove();
        } else if (btn.classList.contains('k-remove-line')) {
            btn.closest('tr.k-line').remove();
        } else if (btn.classList.contains('k-remove-shared')) {
            btn.closest('tr.k-share').remove();
        } else if (btn.classList.contains('k-add-line')) {
            addLine(body).querySelector('input').focus();
            icons(); number();
            return;
        } else if (btn.classList.contains('k-toggle-lines')) {
            var row = body.querySelector('.k-lines-row');
            if (!body.querySelector('tr.k-line')) { addLine(body).querySelector('input').focus(); icons(); number(); return; }
            row.hidden = !row.hidden;
            btn.setAttribute('aria-expanded', String(!row.hidden));
            return;
        } else if (btn.classList.contains('k-add-item')) {
            addItem().querySelector('.k-name').focus();
            icons(); number();
            return;
        } else if (btn.classList.contains('k-add-shared')) {
            var tr = fromTemplate('k-shared-template', 'tr');
            shared.querySelector('tbody').appendChild(tr);
            icons(); number();
            tr.querySelector('input').focus();
            return;
        } else {
            return;
        }
        number();
        preview();
    });

    form.addEventListener('input', function (e) {
        var t = e.target;
        if (t.name === 'sheet_json' || t.name === 'notes' || t.name === 'template_id') return;
        if (t.closest('.k-over-items')) return;
        if (t.classList.contains('k-desc')) { t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; }
        if (t.dataset.k === 'description' && t.list && e.inputType !== 'insertText' && e.inputType !== 'deleteContentBackward') applyRate(t);
        preview();
    });
    form.addEventListener('change', function (e) {
        var t = e.target;
        if (t.closest('.k-over-items')) {
            var tr = t.closest('tr.k-share');
            tr.dataset.items = JSON.stringify(Array.prototype.filter.call(tr.querySelectorAll('.k-over-items input'), function (cb) {
                return cb.checked; }).map(function (cb) { return cb.value; }));
            pickers(tr);
            preview();
            return;
        }
        if (t.dataset.k === 'kind') { t.closest('tr.k-share').dataset.kind = t.value; preview(); }
        if (t.dataset.k === 'spread') preview();
        if (t.dataset.k === 'description' && t.list) { applyRate(t); preview(); }
        if (t.classList.contains('k-name')) sharedRows().forEach(pickers);
        if (t.name === 'mode') setMode();
        if (t.name === 'currency') setCurrency();
        if (t.name === 'mode' || t.name === 'round_to' || t.name === 'currency') preview();
    });
    form.addEventListener('submit', function () { sheetInput.value = JSON.stringify(collect()); });

    function autosize() {
        form.querySelectorAll('.k-desc').forEach(function (t) { if (t.value) { t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; } });
    }

    if (!table.querySelector('tbody.k-item')) addItem();
    autosize();
    setMode();
    setCurrency();
    icons();
    number();

    window.KCosting = {
        items: function () {
            return itemBodies().map(function (body, i) {
                return { body: body, label: (i + 1) + '. ' + (val(body.querySelector('.k-item-row'), 'name').trim() || 'Item ' + (i + 1)) };
            });
        },
        addItems: addItems,
        addLinesTo: addLinesTo,
        base: base
    };
})();
