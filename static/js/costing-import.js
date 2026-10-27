// Costing editor, adding rows from elsewhere: items copied from an earlier costing, or rows
// picked out of a spreadsheet (the server reads the workbook into grids; the mapping is done here).
(function () {
    var K = window.KCosting;
    if (!K) return;

    function el(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text !== undefined && text !== null) e.textContent = text;
        return e;
    }
    function icons() { if (window.lucide) window.lucide.createIcons(); }
    function money(v, cur) {
        if (v === null || v === undefined || !isFinite(v)) return '';
        try { return new Intl.NumberFormat(cur === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency: cur || 'INR' }).format(v); }
        catch (e) { return Number(v).toFixed(2); }
    }
    function openDialog(d) { if (d.showModal) d.showModal(); else d.setAttribute('open', ''); }
    function closeDialog(d) { if (d.close) d.close(); else d.removeAttribute('open'); }

    document.querySelectorAll('[data-open]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var d = document.getElementById(btn.dataset.open);
            d.dispatchEvent(new CustomEvent('k-open'));
            openDialog(d);
        });
    });
    document.querySelectorAll('.k-dialog').forEach(function (d) {
        d.addEventListener('click', function (e) {
            if (e.target.closest('[data-close]') || e.target === d) closeDialog(d);     // the backdrop closes it too
        });
    });

    // ------------------------------------------------------------ Copy from a costing
    (function () {
        var d = document.getElementById('k-copy');
        if (!d) return;
        var list = d.querySelector('[data-list]'), search = d.querySelector('[data-search]'), empty = d.querySelector('[data-empty]');
        var pick = d.querySelector('[data-step="pick"]'), step2 = d.querySelector('[data-step="items"]');
        var itemsList = d.querySelector('[data-items-list]'), all = d.querySelector('[data-all]');
        var add = d.querySelector('[data-add]'), back = d.querySelector('[data-back]');
        var loaded = [], timer = null;

        function showStep(which) {
            pick.hidden = which !== 'pick';
            step2.hidden = which !== 'items';
            back.hidden = which !== 'items';
            add.disabled = which !== 'items';
        }
        function load() {
            fetch(d.dataset.library + '?q=' + encodeURIComponent(search.value.trim()), { credentials: 'same-origin' })
                .then(function (r) { return r.json(); })
                .then(function (rows) {
                    rows = rows.filter(function (r) { return r.costing_id !== d.dataset.self && r.items > 0; });
                    list.innerHTML = '';
                    empty.hidden = rows.length > 0;
                    rows.forEach(function (r) {
                        var li = el('li'), btn = el('button', 'k-pick-row');
                        btn.type = 'button';
                        var main = el('span', 'pick-main');
                        main.appendChild(el('span', 'pick-title', r.title + ' · v' + r.version));
                        main.appendChild(el('span', 'pick-sub', [r.project, r.customer, r.items + (r.items === 1 ? ' item' : ' items'),
                                                                 money(r.total, r.currency)].filter(Boolean).join(' · ')));
                        btn.appendChild(main);
                        btn.addEventListener('click', function () { choose(r); });
                        li.appendChild(btn);
                        list.appendChild(li);
                    });
                });
        }
        function choose(r) {
            fetch(d.dataset.items.replace('COSTING', r.costing_id), { credentials: 'same-origin' })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    loaded = data.items;
                    d.querySelector('[data-source]').textContent = r.title + ' · v' + r.version + (r.project ? ' · ' + r.project : '');
                    itemsList.innerHTML = '';
                    loaded.forEach(function (it, i) {
                        var li = el('li'), label = el('label', 'k-check');
                        var cb = el('input');
                        cb.type = 'checkbox'; cb.checked = true; cb.value = i;
                        var text = el('span', null, it.name || 'Item ' + (i + 1));
                        var sub = el('span', 'k-check-sub', [it.qty !== null ? 'Qty ' + it.qty : '',
                            it.own_cost_each ? money(it.own_cost_each, data.cost_currency) + ' each' : '',
                            it.lines.length ? it.lines.length + (it.lines.length === 1 ? ' cost line' : ' cost lines') : ''].filter(Boolean).join(' · '));
                        label.appendChild(cb); label.appendChild(text); label.appendChild(sub);
                        li.appendChild(label);
                        itemsList.appendChild(li);
                    });
                    all.checked = true;
                    count();
                    showStep('items');
                });
        }
        function boxes() { return Array.prototype.slice.call(itemsList.querySelectorAll('input[type="checkbox"]')); }
        function count() {
            var n = boxes().filter(function (b) { return b.checked; }).length;
            add.textContent = n ? 'Add ' + n + (n === 1 ? ' item' : ' items') : 'Add items';
            add.disabled = !n;
        }

        d.addEventListener('k-open', function () { search.value = ''; showStep('pick'); load(); setTimeout(function () { search.focus(); }, 0); });
        search.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(load, 200); });
        all.addEventListener('change', function () { boxes().forEach(function (b) { b.checked = all.checked; }); count(); });
        itemsList.addEventListener('change', count);
        back.addEventListener('click', function () { showStep('pick'); });
        add.addEventListener('click', function () {
            var picked = boxes().filter(function (b) { return b.checked; }).map(function (b) {
                var it = loaded[+b.value];
                // Typed prices belong to that quote; here they're worked out again
                return { name: it.name, description: it.description, qty: it.qty, unit: it.unit, cost_each: it.cost_each,
                         profit_percent: it.profit_percent, lines: it.lines };
            });
            K.addItems(picked);
            closeDialog(d);
        });
    })();

    // ------------------------------------------------------------ Import from Excel
    (function () {
        var d = document.getElementById('k-import');
        if (!d) return;
        var fileInput = d.querySelector('[data-file]'), error = d.querySelector('[data-error]');
        var stepFile = d.querySelector('[data-step="file"]'), stepMap = d.querySelector('[data-step="map"]');
        var sheetSelect = d.querySelector('[data-sheet]'), headerInput = d.querySelector('[data-header]');
        var cols = {};
        d.querySelectorAll('[data-col]').forEach(function (s) { cols[s.dataset.col] = s; });
        var into = d.querySelector('[data-into]'), newItem = d.querySelector('[data-new-item]'), prices = d.querySelector('[data-prices]');
        var add = d.querySelector('[data-add]'), restart = d.querySelector('[data-restart]');
        var data = null;
        var TOTALS = /^(sub[\s-]*)?total\b|grand\s*total|^net\s*(total|amount)|^profit\b|^margin\b|^(c|s|i)?gst\b|^tax\b|^discount\b|^round(ed|ing)?\s*off/i;

        function letter(j) { return String.fromCharCode(65 + j); }
        function text(v) { return v === null || v === undefined ? '' : String(v).trim(); }
        function number(v) {
            if (typeof v === 'number') return isFinite(v) ? v : null;
            var s = text(v).replace(/[,\s₹$]/g, '').replace(/^rs\.?/i, '');
            return /^-?\d+(\.\d+)?$/.test(s) ? parseFloat(s) : null;
        }
        function sheet() { return data.sheets[+sheetSelect.value || 0]; }
        function header() { return Math.max(0, (parseInt(headerInput.value, 10) || 1) - 1); }
        function as() { return (d.querySelector('[name="k-im-as"]:checked') || {}).value || 'items'; }

        function showStep(which) {
            stepFile.hidden = which !== 'file';
            stepMap.hidden = which !== 'map';
            restart.hidden = which !== 'map';
            if (which === 'file') add.disabled = true;
        }
        function reset() {
            data = null; fileInput.value = ''; error.hidden = true;
            showStep('file');
        }

        function columnOptions() {
            var s = sheet(), head = s.rows[header()] || [], width = s.rows.reduce(function (w, r) { return Math.max(w, r.length); }, 0);
            Object.keys(cols).forEach(function (key) {
                var select = cols[key], keep = select.value;
                select.innerHTML = '';
                select.appendChild(new Option('—', '-1'));
                for (var j = 0; j < width; j++) {
                    var label = text(head[j]);
                    select.appendChild(new Option(letter(j) + (label ? ' · ' + label.slice(0, 28) : ''), String(j)));
                }
                select.value = keep !== '' && keep !== null && select.querySelector('option[value="' + keep + '"]') ? keep : '-1';
            });
        }
        function useSheet() {
            var s = sheet();
            headerInput.value = (s.header_row === null || s.header_row === undefined ? 0 : s.header_row) + 1;
            Object.keys(cols).forEach(function (k) { cols[k].value = ''; });
            columnOptions();
            Object.keys(cols).forEach(function (k) {
                var j = s.columns[k];
                cols[k].value = j === undefined ? '-1' : String(j);
            });
            newItem.value = s.name;
            render();
        }

        function rows() {
            var s = sheet(), c = {}, out = [], skipped = 0;
            Object.keys(cols).forEach(function (k) { c[k] = parseInt(cols[k].value, 10); });
            function at(r, k) { return c[k] >= 0 ? r[c[k]] : null; }
            for (var i = header() + 1; i < s.rows.length; i++) {
                var r = s.rows[i];
                var name = text(at(r, 'name')), spec = text(at(r, 'spec')), unit = text(at(r, 'unit'));
                var qty = number(at(r, 'qty')), price = number(at(r, 'price')), amount = number(at(r, 'amount'));
                if (!name && !spec && qty === null && price === null && amount === null) continue;   // blank rows don't count
                if (!name && spec) { name = spec; spec = ''; }
                if (!name || TOTALS.test(name) || (price === null && amount === null)) { skipped++; continue; }
                if (price === null) price = qty ? amount / qty : amount;
                out.push({ name: name, spec: spec, qty: qty, unit: unit, price: Math.round(price * 10000) / 10000 });
            }
            return { rows: out, skipped: skipped };
        }

        function render() {
            var mode = as();
            d.querySelectorAll('.k-im-items-only').forEach(function (e) { e.hidden = mode !== 'items'; });
            var got = rows(), head = d.querySelector('[data-preview-head]'), body = d.querySelector('[data-preview-body]');
            var names = mode === 'items' ? ['Item', 'Description', 'Qty', 'Unit', prices.value === 'price' ? 'Price / unit' : 'Cost / unit']
                                         : ['Cost line', 'Make / spec', 'Qty', 'Unit', 'Unit cost'];
            head.innerHTML = '';
            var tr = el('tr');
            names.forEach(function (n, i) { tr.appendChild(el('th', i >= 2 ? (i === 4 ? 'num' : '') : (i === 0 ? 'long' : ''), n)); });
            head.appendChild(tr);
            body.innerHTML = '';
            got.rows.slice(0, 8).forEach(function (r) {
                var row = el('tr');
                [r.name, r.spec, r.qty === null ? '' : r.qty, r.unit, money(r.price, K.base)].forEach(function (v, i) {
                    row.appendChild(el('td', i === 4 ? 'num' : (i === 0 ? 'long' : ''), v));
                });
                body.appendChild(row);
            });
            var n = got.rows.length, more = n > 8 ? ' (the first 8 are shown)' : '';
            d.querySelector('[data-summary]').textContent = n
                ? n + (n === 1 ? ' row' : ' rows') + ' to add' + more + (got.skipped ? '. ' + got.skipped + ' skipped: totals, or no amount.' : '.')
                : 'No rows with an item and an amount under that heading row. Check the sheet, the heading row and the columns.';
            add.disabled = !n || (mode === 'into' && !into.value);
            add.textContent = n ? 'Add ' + n + (mode === 'items' ? (n === 1 ? ' item' : ' items') : (n === 1 ? ' cost line' : ' cost lines')) : 'Add rows';
        }

        function fillInto() {
            into.innerHTML = '';
            K.items().forEach(function (it, i) { into.appendChild(new Option(it.label, String(i))); });
            var radio = d.querySelector('[name="k-im-as"][value="into"]');
            radio.disabled = !into.options.length;
            if (radio.disabled && radio.checked) d.querySelector('[name="k-im-as"][value="items"]').checked = true;
        }

        fileInput.addEventListener('change', function () {
            var file = fileInput.files[0];
            if (!file) return;
            error.hidden = true;
            var body = new FormData();
            body.append('file', file);
            d.querySelector('.k-drop').classList.add('busy');
            fetch(d.dataset.url, { method: 'POST', body: body, credentials: 'same-origin' })
                .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, json: j }; }); })
                .then(function (res) {
                    if (!res.ok) throw new Error(res.json.error || 'That file could not be read.');
                    data = res.json;
                    sheetSelect.innerHTML = '';
                    data.sheets.forEach(function (s, i) { sheetSelect.appendChild(new Option(s.name, String(i))); });
                    // Start on the first sheet that looks like a costing
                    var first = data.sheets.findIndex(function (s) { return s.header_row !== null && s.columns.name !== undefined; });
                    sheetSelect.value = String(Math.max(0, first));
                    d.querySelector('[data-file-name]').textContent = data.file;
                    fillInto();
                    useSheet();
                    showStep('map');
                })
                .catch(function (e) { error.textContent = e.message; error.hidden = false; fileInput.value = ''; })
                .then(function () { d.querySelector('.k-drop').classList.remove('busy'); });
        });
        sheetSelect.addEventListener('change', useSheet);
        headerInput.addEventListener('input', function () { columnOptions(); render(); });
        stepMap.addEventListener('change', function (e) { if (e.target !== sheetSelect) render(); });
        newItem.addEventListener('focus', function () { d.querySelector('[name="k-im-as"][value="lines"]').checked = true; render(); });
        into.addEventListener('focus', function () { d.querySelector('[name="k-im-as"][value="into"]').checked = true; render(); });
        restart.addEventListener('click', reset);
        d.addEventListener('k-open', function () { if (data) { fillInto(); render(); } });

        add.addEventListener('click', function () {
            var got = rows().rows, mode = as();
            var lines = got.map(function (r) { return { description: r.name, make: r.spec, qty: r.qty, unit: r.unit, unit_cost: r.price }; });
            if (mode === 'items') {
                var cost = prices.value !== 'price';
                K.addItems(got.map(function (r) {
                    return { name: r.name, description: r.spec, qty: r.qty, unit: r.unit,
                             cost_each: cost ? r.price : null, price_each: cost ? null : r.price };
                }));
            } else if (mode === 'lines') {
                K.addItems([{ name: newItem.value.trim() || sheet().name, qty: 1, lines: lines }]);
            } else {
                var target = K.items()[+into.value];
                if (target) K.addLinesTo(target.body, lines);
            }
            closeDialog(d);
            reset();
        });
    })();

    icons();
})();
