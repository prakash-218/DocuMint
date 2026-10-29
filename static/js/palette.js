// Ctrl+K (⌘K on a Mac), or the Search button: find a page, document, project, customer or template by typing
// a little of it, and open it with Enter (Ctrl+Enter: in a new tab). What it can find comes from /search/items
// (search.py), the first time it opens on a page. The matching is fuzzy.js, as in the project picker:
// 'trq fixtre' finds "Torque fixture", 'q29' finds TF/Q/029/26-27, 'acme 26-27' Acme's documents that year.
(function (root) {
    var Fuzzy = root.Fuzzy || require('./fuzzy.js');
    var SHOWN = 20;
    var RECENT_KEY = 'documint.recent', RECENT_MAX = 5;
    var ORDER = { page: 0, action: 1, command: 2, project: 3, customer: 4, document: 5, template: 6 };

    // '029r1' is also '29r1', and (without the revision) '029' and '29'
    function forms(w) {
        var out = [w], head = w.match(/^(\d+)[a-z]/);
        if (head) out.push(head[1]);
        out.slice().forEach(function (f) {
            var bare = f.replace(/^0+(?=\d)/, '');
            if (bare !== f) out.push(bare);
        });
        return out;
    }

    // 'TF/Q/029R1/26-27': its words in all their forms, and each run into the next ('q029r1', 'q29'),
    // so '29', 'q29' and 'Q/029' all find it (and its revisions, newest first)
    function codeWords(text) {
        var list = Fuzzy.words(text), out = [];
        list.forEach(function (w, i) {
            out = out.concat(forms(w));
            if (list[i + 1]) forms(list[i + 1]).forEach(function (f) { out.push(w + f); });
        });
        return out;
    }

    // Every word typed has to match; matches in the name or number count most. The few pages and actions
    // come before the many documents that mention the same word.
    function score(item, tokens) {
        if (!tokens.length) return 0;
        var name = item._name || (item._name = Fuzzy.words(item.name).concat(codeWords(item.code)));
        var also = item._also || (item._also = Fuzzy.words(item.also));
        var total = 0;
        for (var i = 0; i < tokens.length; i++) {
            var inName = Fuzzy.wordScore(tokens[i], name);
            var s = Math.max(inName ? inName + 2 : 0, Fuzzy.wordScore(tokens[i], also));
            if (!s) return null;
            total += s;
        }
        return total + (ORDER[item.kind] <= ORDER.command ? 3 : 0);
    }

    // The items that match, best first; on a tie current ones before old ones, then the most recent
    function rank(items, query) {
        var tokens = Fuzzy.words(query), hits = [];
        items.forEach(function (item) {
            var s = score(item, tokens);
            if (s !== null) hits.push({ item: item, score: s });
        });
        hits.sort(function (a, b) {
            return (b.score - a.score) || ((a.item.old ? 1 : 0) - (b.item.old ? 1 : 0)) ||
                (b.item.date || '').localeCompare(a.item.date || '') || (ORDER[a.item.kind] - ORDER[b.item.kind]);
        });
        return hits.map(function (h) { return h.item; });
    }

    if (typeof module === 'object' && module.exports) {       // the tests run the matching in Node
        module.exports = { codeWords: codeWords, score: score, rank: rank };
        return;
    }

    var dialog = document.getElementById('palette');
    if (!dialog) return;
    var input = dialog.querySelector('.palette-query');
    var list = dialog.querySelector('.palette-list');
    var more = dialog.querySelector('.palette-more');
    var COMMANDS = [{ kind: 'command', title: 'Dark mode on / off', icon: 'moon', name: 'dark light mode theme night',
                      run: function () { if (root.toggleTheme) root.toggleTheme(); } }];
    var items = null, loading = false, failed = false, shown = [], options = [], active = -1, icons = {};

    if (/Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent)) {
        document.querySelectorAll('[data-palette-key]').forEach(function (k) { k.textContent = k.textContent.replace('Ctrl', '⌘'); });
    }

    function el(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text != null) e.textContent = text;
        return e;
    }

    function icon(name) {
        if (!icons[name]) {
            var key = name.replace(/(^|-)(\w)/g, function (m, dash, c) { return c.toUpperCase(); });
            var node = root.lucide && root.lucide.icons && root.lucide.icons[key];
            if (!node) return el('span', 'palette-icon');
            icons[name] = root.lucide.createElement(node);
            icons[name].setAttribute('class', 'lucide lucide-' + name);
        }
        var box = el('span', 'palette-icon');
        box.appendChild(icons[name].cloneNode(true));
        return box;
    }

    function recent() {
        try { return JSON.parse(root.localStorage.getItem(RECENT_KEY) || '[]'); } catch (e) { return []; }
    }

    function remember(item) {
        if (!item.url || ORDER[item.kind] <= ORDER.command) return;    // pages are always listed anyway
        var urls = [item.url].concat(recent().filter(function (u) { return u !== item.url; })).slice(0, RECENT_MAX);
        try { root.localStorage.setItem(RECENT_KEY, JSON.stringify(urls)); } catch (e) { /* not remembered */ }
    }

    function load() {
        if (items || loading) return;
        loading = true;
        failed = false;
        fetch(dialog.dataset.source, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (data) { items = (data.items || []).concat(COMMANDS); })
            .catch(function () { failed = true; })
            .then(function () { loading = false; if (dialog.open) render(); });
    }

    function heading(text) {
        var li = el('li', 'palette-group', text);
        li.setAttribute('role', 'presentation');
        list.appendChild(li);
    }

    function option(item) {
        var i = shown.length;
        shown.push(item);
        var li = el('li');
        li.setAttribute('role', 'presentation');
        var a = el('a', 'palette-option');
        a.id = 'palette-option-' + i;
        a.href = item.url || '#';
        a.tabIndex = -1;
        a.setAttribute('role', 'option');
        a.appendChild(icon(item.icon || 'file'));
        var main = el('span', 'palette-main');
        main.appendChild(el('span', 'palette-title', item.title));
        if (item.sub) main.appendChild(el('span', 'palette-sub', item.sub));
        a.appendChild(main);
        if (item.badge) a.appendChild(el('span', 'badge badge-' + (item.tone || 'secondary'), item.badge));
        a.addEventListener('mousedown', function (e) { e.preventDefault(); });   // keep the focus in the search box
        a.addEventListener('mousemove', function () { if (active !== i) { active = i; mark(); } });
        a.addEventListener('click', function (e) {
            if (item.run) { e.preventDefault(); dialog.close(); item.run(); return; }
            remember(item);
            if (!(e.ctrlKey || e.metaKey || e.shiftKey)) dialog.close();           // the link opens; a new tab leaves this open
        });
        options.push(a);
        li.appendChild(a);
        list.appendChild(li);
    }

    function render() {
        list.innerHTML = '';
        shown = [];
        options = [];
        more.hidden = true;
        if (!items) {
            list.appendChild(el('li', 'palette-empty', failed ? 'Could not load the search. Close it and press Ctrl+K to try again.' : 'Loading…'));
            active = -1;
            mark();
            return;
        }
        if (!Fuzzy.words(input.value).length) {
            var byUrl = {};
            items.forEach(function (it) { if (it.url) byUrl[it.url] = it; });
            var picked = recent().map(function (u) { return byUrl[u]; }).filter(Boolean);
            if (picked.length) { heading('Recent'); picked.forEach(option); }
            heading('Go to');
            items.filter(function (it) { return it.kind === 'page'; }).forEach(option);
            heading('Actions');
            items.filter(function (it) { return it.kind === 'action' || it.kind === 'command'; }).forEach(option);
        } else {
            var hits = rank(items, input.value);
            hits.slice(0, SHOWN).forEach(option);
            if (!hits.length) list.appendChild(el('li', 'palette-empty', 'Nothing matches. Try fewer letters, or another word.'));
            var rest = hits.length - shown.length;
            more.hidden = rest <= 0;
            more.textContent = rest > 0 ? rest + ' more. Type more to narrow them down.' : '';
        }
        active = shown.length ? 0 : -1;
        list.scrollTop = 0;
        mark();
    }

    function mark() {
        options.forEach(function (a, i) {
            a.classList.toggle('is-active', i === active);
            a.setAttribute('aria-selected', i === active ? 'true' : 'false');
        });
        if (active >= 0) input.setAttribute('aria-activedescendant', options[active].id);
        else input.removeAttribute('aria-activedescendant');
    }

    function go(item, newTab) {
        if (item.run) { dialog.close(); item.run(); return; }
        remember(item);
        if (newTab) { root.open(item.url, '_blank'); return; }
        dialog.close();
        if (root.dmNavigate) root.dmNavigate(item.url);    // the React app opens its own screens without a page load
        else root.location = item.url;
    }

    function open() {
        if (dialog.open) return;
        dialog.showModal();
        input.select();
        if (!items) load();
        render();
    }

    input.addEventListener('input', render);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            if (!shown.length) return;
            active = (active + (e.key === 'ArrowDown' ? 1 : -1) + shown.length) % shown.length;
            mark();
            options[active].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (active >= 0) go(shown[active], e.ctrlKey || e.metaKey || e.shiftKey);
        }
    });

    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && (e.key === 'k' || e.key === 'K' || e.code === 'KeyK')) {
            e.preventDefault();
            if (dialog.open) dialog.close(); else open();
        }
    });
    // The search buttons, wherever they are (the React app draws its own after this runs)
    function opener(e) { return e.target && e.target.closest ? e.target.closest('[data-palette-open]') : null; }
    document.addEventListener('click', function (e) { if (opener(e)) open(); });
    document.addEventListener('mouseover', function (e) { if (opener(e)) load(); });     // start loading before the click
    document.addEventListener('focusin', function (e) { if (opener(e)) load(); });
    // Back to a page the search left from: don't show it still open
    root.addEventListener('pageshow', function (e) { if (e.persisted && dialog.open) dialog.close(); });
})(this);
