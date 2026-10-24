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
                if (e.target.closest('a, button, input, select, form, label')) return;
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
