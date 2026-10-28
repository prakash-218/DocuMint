// Project picker: search a list of projects by name, number or customer (forgiving typos and
// abbreviations), narrow it by financial year, and pick one with a click or the keyboard.
//
// <div data-project-picker data-source="/projects/options?..."> with the markup from the
// project_picker macro (templates/_macros.html). Picking a project either submits the picker's
// form with project_id set (the default), or, with data-href=".../__ID__", goes to that page.
// data-current marks the project the thing is in now; data-prefer (a customer id) lists that
// customer's projects first.
//
// The matching is the same as projects.match_score in Python (the projects page): keep them alike.
(function () {
    var SHOWN = 8;
    var FY_KEY = 'documint.pickerFy';

    function words(text) {
        return String(text || '').normalize('NFKD').replace(/[^\x00-\x7f]/g, '').toLowerCase().match(/[a-z0-9]+/g) || [];
    }

    function oneEditApart(a, b) {
        if (a === b) return true;
        if (Math.abs(a.length - b.length) > 1) return false;
        var i;
        if (a.length === b.length) {
            var diff = [];
            for (i = 0; i < a.length; i++) if (a[i] !== b[i]) diff.push(i);
            return diff.length === 1 || (diff.length === 2 && diff[1] === diff[0] + 1 &&
                a[diff[0]] === b[diff[1]] && a[diff[1]] === b[diff[0]]);
        }
        var s = a.length < b.length ? a : b, l = a.length < b.length ? b : a;
        for (i = 0; i < s.length && s[i] === l[i]; i++) { /* first difference */ }
        return s.slice(i) === l.slice(i + 1);
    }

    function inOrder(token, word) {
        var at = 0;
        for (var i = 0; i < token.length; i++) {
            at = word.indexOf(token[i], at);
            if (at < 0) return false;
            at += 1;
        }
        return true;
    }

    function wordScore(token, list) {
        var best = 0;
        for (var i = 0; i < list.length; i++) {
            var w = list[i], score = 0;
            if (w === token) return 10;
            if (w.indexOf(token) === 0) score = 8;
            else if (w.indexOf(token) >= 0) score = 5;
            else if (token.length >= 4 && (oneEditApart(token, w) || oneEditApart(token, w.slice(0, token.length)))) score = 4;
            else if (token.length >= 2 && w[0] === token[0] && inOrder(token, w)) score = 3;
            if (score > best) best = score;
        }
        return best;
    }

    function matchScore(p, tokens) {
        if (!tokens.length) return 0;
        var title = p._title || (p._title = words(p.title));
        var other = p._other || (p._other = words([p.customer, p.site, p.reference].join(' ')).concat(['prj']));
        var total = 0;
        for (var i = 0; i < tokens.length; i++) {
            var t = tokens[i], digits = t.replace(/^prj/, '');
            if (/^\d+$/.test(digits) && digits.replace(/^0+/, '') === String(p.project_no)) { total += 15; continue; }
            var inTitle = wordScore(t, title);
            var score = Math.max(inTitle ? inTitle + 2 : 0, wordScore(t, other));
            if (!score) return null;
            total += score;
        }
        return total;
    }

    function el(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text != null) e.textContent = text;
        return e;
    }

    function init(root) {
        if (root.dataset.ready) return;
        root.dataset.ready = '1';
        var input = root.querySelector('.pp-query');
        var fySelect = root.querySelector('.pp-fy');
        var list = root.querySelector('.pp-list');
        var more = root.querySelector('.pp-more');
        var prefer = root.dataset.prefer || '';
        var projects = null, shown = [], active = -1, loading = false;

        function load() {
            if (projects || loading) return;
            loading = true;
            fetch(root.dataset.source, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
                .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                .then(function (data) {
                    projects = data.projects || [];
                    var years = [];
                    projects.forEach(function (p) { if (p.fy && years.indexOf(p.fy) < 0) years.push(p.fy); });
                    years.sort().reverse();
                    years.forEach(function (y) { fySelect.appendChild(new Option('FY ' + y, y)); });
                    var saved = '';
                    try { saved = window.localStorage.getItem(FY_KEY) || ''; } catch (e) { /* not remembered */ }
                    if (saved && years.indexOf(saved) >= 0) fySelect.value = saved;
                    fySelect.hidden = !years.length;
                    render();
                })
                .catch(function () {
                    list.innerHTML = '';
                    list.appendChild(el('li', 'pp-empty', 'Could not load the projects. Reload the page to try again.'));
                });
        }

        function render() {
            var tokens = words(input.value), fy = fySelect.value;
            var hits = [];
            projects.forEach(function (p) {
                if (fy && p.fy !== fy) return;
                var score = matchScore(p, tokens);
                if (score !== null) hits.push({ p: p, score: score });
            });
            hits.sort(function (a, b) {
                return (b.score - a.score) ||
                    ((a.p.status !== 'open') - (b.p.status !== 'open')) ||
                    ((prefer && a.p.customer_id !== prefer) - (prefer && b.p.customer_id !== prefer)) ||
                    (b.p.last || '').localeCompare(a.p.last || '') ||
                    (b.p.project_no - a.p.project_no);
            });
            shown = hits.slice(0, SHOWN).map(function (h) { return h.p; });
            active = shown.length ? 0 : -1;
            list.innerHTML = '';
            if (!shown.length) {
                list.appendChild(el('li', 'pp-empty', projects.length ? 'No project matches. Try fewer letters, or another year.' : 'No projects yet.'));
            }
            shown.forEach(function (p, i) {
                var li = el('li', 'pp-option');
                li.id = list.id + '-' + i;
                li.setAttribute('role', 'option');
                var main = el('span', 'pp-main');
                main.appendChild(el('span', 'pp-title', p.title));
                var meta = [p.no, p.site ? p.customer + ' · ' + p.site : p.customer, p.fy ? 'FY ' + p.fy : '',
                            p.docs ? p.docs + (p.docs === 1 ? ' document' : ' documents') : ''].filter(Boolean).join(' · ');
                main.appendChild(el('span', 'pp-sub', meta));
                li.appendChild(main);
                if (p.id === (root.dataset.current || '')) li.appendChild(el('span', 'badge badge-info', 'Current'));
                else if (p.status !== 'open') li.appendChild(el('span', 'badge badge-secondary', p.status === 'completed' ? 'Completed' : 'Cancelled'));
                li.addEventListener('mousedown', function (e) { e.preventDefault(); });   // keep the focus in the search box
                li.addEventListener('click', function () { pick(p); });
                li.addEventListener('mousemove', function () { if (active !== i) { active = i; mark(); } });
                list.appendChild(li);
            });
            var rest = hits.length - shown.length;
            more.hidden = rest <= 0;
            more.textContent = rest > 0 ? rest + ' more ' + (rest === 1 ? 'match' : 'matches') + '. Type more of the name to narrow them down.' : '';
            mark();
        }

        function mark() {
            Array.prototype.forEach.call(list.querySelectorAll('.pp-option'), function (li, i) {
                li.classList.toggle('is-active', i === active);
                li.setAttribute('aria-selected', i === active ? 'true' : 'false');
            });
            if (active >= 0) input.setAttribute('aria-activedescendant', list.id + '-' + active);
            else input.removeAttribute('aria-activedescendant');
        }

        function pick(p) {
            if (p.id === (root.dataset.current || '')) return;
            if (root.dataset.href) {
                window.location = root.dataset.href.replace('__ID__', encodeURIComponent(p.id));
                return;
            }
            var form = root.closest('form');
            var field = form.querySelector('input[data-picked]');
            if (!field) {
                field = el('input');
                field.type = 'hidden';
                field.name = root.dataset.name || 'project_id';
                field.setAttribute('data-picked', '');
                form.appendChild(field);
            }
            field.value = p.id;
            list.classList.add('is-busy');
            if (form.requestSubmit) form.requestSubmit(); else form.submit();
        }

        input.addEventListener('input', function () { if (projects) render(); });
        input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                if (!shown.length) return;
                e.preventDefault();
                active = (active + (e.key === 'ArrowDown' ? 1 : -1) + shown.length) % shown.length;
                mark();
                var li = list.children[active];
                if (li && li.scrollIntoView) li.scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter') {
                e.preventDefault();             // never submit the form without a project
                if (active >= 0) pick(shown[active]);
            } else if (e.key === 'Escape' && input.value) {
                e.preventDefault();
                e.stopPropagation();
                input.value = '';
                render();
            }
        });
        fySelect.addEventListener('change', function () {
            try { window.localStorage.setItem(FY_KEY, fySelect.value); } catch (e) { /* not remembered */ }
            if (projects) render();
            input.focus();
        });
        root.addEventListener('focusin', load);

        // Load the list once the picker is on screen (in a closed <details> or <dialog> it isn't yet)
        if ('IntersectionObserver' in window) {
            var seen = new IntersectionObserver(function (entries) {
                if (entries.some(function (e) { return e.isIntersecting; })) { seen.disconnect(); load(); }
            });
            seen.observe(root);
        } else {
            load();
        }
    }

    window.ProjectPicker = { init: init, matchScore: matchScore, words: words };

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-project-picker]').forEach(init);

        // <details class="pp-toggle">: focus the search when it opens
        document.querySelectorAll('details.pp-toggle').forEach(function (d) {
            d.addEventListener('toggle', function () {
                var q = d.open && d.querySelector('.pp-query');
                if (q) q.focus();
            });
        });

        // Files: "Move" opens one picker dialog for that file
        var dialog = document.getElementById('file-move-dialog');
        if (dialog) {
            var form = dialog.querySelector('form');
            var picker = dialog.querySelector('[data-project-picker]');
            document.addEventListener('click', function (e) {
                var btn = e.target.closest('[data-move-file]');
                if (!btn) return;
                form.action = btn.dataset.moveFile;
                picker.dataset.current = btn.dataset.current || '';
                dialog.querySelector('.file-move-name').textContent = btn.dataset.fileName || 'this file';
                dialog.querySelector('[data-unlink]').hidden = !btn.dataset.current;
                dialog.showModal();
                var q = dialog.querySelector('.pp-query');
                q.value = '';
                q.dispatchEvent(new Event('input'));
                q.focus();
            });                                     // closing: app.js ([data-close], the backdrop, Escape)
        }
    });
})();
