// Shared UI behaviour: icons, theme toggle, mobile sidebar, clickable rows, confirmations.
(function () {
    function initIcons() {
        if (window.lucide) window.lucide.createIcons();
    }

    window.toggleTheme = function () {
        var root = document.documentElement;
        var current = root.getAttribute('data-theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        var next = current === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('dm-theme', next); } catch (e) {}
    };

    window.toggleSidebar = function (force) {
        var sidebar = document.getElementById('sidebar');
        var overlay = document.getElementById('sidebarOverlay');
        if (!sidebar || !overlay) return;
        var open = typeof force === 'boolean' ? force : !sidebar.classList.contains('open');
        sidebar.classList.toggle('open', open);
        overlay.classList.toggle('active', open);
        document.body.style.overflow = open ? 'hidden' : '';
    };

    document.addEventListener('DOMContentLoaded', function () {
        initIcons();

        var overlay = document.getElementById('sidebarOverlay');
        if (overlay) overlay.addEventListener('click', function () { window.toggleSidebar(false); });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') window.toggleSidebar(false);
        });
        window.addEventListener('resize', function () {
            if (window.innerWidth > 768) window.toggleSidebar(false);
        });

        // <tr data-href="..."> rows act as links, but not when clicking a control inside them
        document.querySelectorAll('tr[data-href]').forEach(function (row) {
            row.classList.add('row-link');
            row.addEventListener('click', function (e) {
                if (e.target.closest('a, button, input, select, form, label, details')) return;
                window.location = row.getAttribute('data-href');
            });
        });

        // Line-item text boxes grow with their content (multi-line descriptions / break-ups)
        function grow(el) { el.style.height = 'auto'; el.style.height = Math.max(38, el.scrollHeight + 2) + 'px'; }
        document.addEventListener('input', function (e) {
            if (e.target.classList && e.target.classList.contains('line-text')) grow(e.target);
        });
        document.querySelectorAll('textarea.line-text').forEach(grow);

        // <form data-confirm="..."> asks before submitting
        document.querySelectorAll('form[data-confirm]').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                if (!window.confirm(form.getAttribute('data-confirm'))) e.preventDefault();
            });
        });

        // <select data-autosubmit> saves its form as soon as it changes
        document.querySelectorAll('select[data-autosubmit]').forEach(function (select) {
            select.addEventListener('change', function () {
                if (select.form.requestSubmit) select.form.requestSubmit(); else select.form.submit();
            });
        });
    });

    // lucide loads deferred; render icons once it arrives
    window.addEventListener('load', initIcons);
})();

// Header menus (<details class="menu">): close when clicking elsewhere or pressing Escape
document.addEventListener('click', function (e) {
    document.querySelectorAll('details.menu[open]').forEach(function (menu) {
        if (!menu.contains(e.target)) menu.removeAttribute('open');
    });
});
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') document.querySelectorAll('details.menu[open]').forEach(function (m) { m.removeAttribute('open'); });
});

// "Upload one made earlier": open the upload form with that kind picked
document.addEventListener('click', function (e) {
    var link = e.target.closest('[data-upload-kind]');
    if (!link) return;
    var box = document.getElementById('upload');
    if (!box) return;
    e.preventDefault();
    box.open = true;
    var kind = box.querySelector('.upload-kind');
    if (kind) kind.value = link.dataset.uploadKind;
    box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    var file = box.querySelector('input[type=file]');
    if (file) file.focus();
});

// PDF menu: "Print with seal" adds seal=0 to its links when unticked; the choice is remembered on this browser
(function () {
    var KEY = 'documint.pdfSeal';
    document.querySelectorAll('[data-pdf-menu]').forEach(function (menu) {
        var box = menu.querySelector('[data-seal]');
        if (!box) return;
        try { if (window.localStorage.getItem(KEY) === 'off') box.checked = false; } catch (e) { /* storage blocked: default on */ }
        function apply() {
            menu.querySelectorAll('a[data-pdf]').forEach(function (a) {
                var url = new URL(a.getAttribute('href'), window.location.href);
                if (box.checked) url.searchParams.delete('seal'); else url.searchParams.set('seal', '0');
                a.setAttribute('href', url.pathname + url.search);
            });
            try { window.localStorage.setItem(KEY, box.checked ? 'on' : 'off'); } catch (e) { /* not remembered */ }
        }
        box.addEventListener('change', apply);
        apply();
    });
})();

// <button data-open-dialog="id"> opens that <dialog>; [data-close] inside a dialog, or a click on its backdrop, closes it
document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-open-dialog]');
    if (opener) {
        var d = document.getElementById(opener.getAttribute('data-open-dialog'));
        if (d && d.showModal && !d.open) d.showModal();
        return;
    }
    var dialog = e.target.closest('dialog[open]');
    if (dialog && (e.target === dialog || e.target.closest('[data-close]'))) dialog.close();
});

// A link to #id opens the <details> that id is (or is in), and goes to it: "Record payment" -> <details id="payment">
(function () {
    function reveal(hash) {
        var el = hash && hash.length > 1 && document.getElementById(decodeURIComponent(hash.slice(1)));
        var fold = el && el.closest('details');
        if (!fold) return false;
        fold.open = true;
        el.scrollIntoView({ block: 'start', behavior: 'smooth' });
        var field = fold.querySelector('input:not([type=hidden]):not([type=checkbox]), select, textarea');
        if (field) field.focus({ preventScroll: true });
        return true;
    }
    document.addEventListener('click', function (e) {
        var a = e.target.closest('a[href^="#"]');
        if (a && reveal(a.getAttribute('href'))) {
            e.preventDefault();
            history.replaceState(null, '', a.getAttribute('href'));
        }
    });
    reveal(window.location.hash);
})();
