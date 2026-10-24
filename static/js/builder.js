// Template builder: add / remove sections and fields, field names for formulas,
// and the "Document total" choices (number fields in a fields section).
(function () {
    var form = document.querySelector('[data-builder]');
    if (!form) return;
    var list = document.getElementById('sections');
    var count = document.getElementById('section_count');
    var total = document.getElementById('total');

    function slug(text) {
        return (text || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
    }

    function sectionName(card) {
        return card.querySelector('.fixed-name').value || slug(card.querySelector('.section-title').value);
    }

    function refreshRow(tr) {
        var type = tr.querySelector('.field-type').value;
        var number = type === 'number';
        tr.querySelector('.field-money').disabled = !number;
        tr.querySelector('.field-formula').disabled = !number;
        if (!number) { tr.querySelector('.field-money').checked = false; tr.querySelector('.field-formula').value = ''; }
        var fixed = tr.querySelector('.fixed-name').value;
        tr.querySelector('.field-code').textContent = fixed || slug(tr.querySelector('.field-label').value);
    }

    function refreshTotals() {
        var selected = total.value || total.dataset.selected;
        total.innerHTML = '';
        list.querySelectorAll('.builder-section').forEach(function (card) {
            if (card.hidden || card.querySelector('.section-type').value !== 'normal') return;
            var title = card.querySelector('.section-title').value || 'Section';
            card.querySelectorAll('tr[data-field-row]').forEach(function (tr, j) {
                if (tr.hidden || tr.querySelector('.field-type').value !== 'number') return;
                var label = tr.querySelector('.field-label').value;
                if (!label) return;
                var name = tr.querySelector('.field-label').name;          // s<i>_f<j>_label
                var m = name.match(/^s(\d+)_f(\d+)_/);
                var opt = document.createElement('option');
                opt.value = m[1] + ':' + m[2];
                opt.textContent = title + ' › ' + label;
                total.appendChild(opt);
            });
        });
        if (!total.options.length) {
            var none = document.createElement('option');
            none.value = ''; none.textContent = 'Add a number field to a fields section';
            total.appendChild(none);
        }
        if ([].some.call(total.options, function (o) { return o.value === selected; })) total.value = selected;
        else total.value = total.options[total.options.length - 1].value;
    }

    function addField(card) {
        var i = card.dataset.index;
        var fc = card.querySelector('.field-count');
        var j = (parseInt(fc.value, 10) || 0) + 1;
        fc.value = j;
        var html = document.getElementById('field_tpl').innerHTML.replace(/__S__/g, i).replace(/__F__/g, j);
        card.querySelector('tbody').insertAdjacentHTML('beforeend', html);
        var tr = card.querySelector('tbody').lastElementChild;
        refreshRow(tr);
        if (window.lucide) window.lucide.createIcons();
        tr.querySelector('.field-label').focus();
    }

    document.getElementById('add_section').addEventListener('click', function () {
        var i = (parseInt(count.value, 10) || 0) + 1;
        count.value = i;
        var html = document.getElementById('section_tpl').innerHTML.replace(/__S__/g, i);
        list.insertAdjacentHTML('beforeend', html);
        var card = list.lastElementChild;
        card.querySelectorAll('tr[data-field-row]').forEach(refreshRow);
        if (window.lucide) window.lucide.createIcons();
        card.querySelector('.section-title').focus();
        refreshTotals();
    });

    form.addEventListener('click', function (e) {
        var btn = e.target.closest('.add-field');
        if (btn) { addField(btn.closest('.builder-section')); return; }
        btn = e.target.closest('.remove-field');
        if (btn) {
            var tr = btn.closest('tr');
            tr.querySelector('.present').value = '';
            tr.hidden = true;
            refreshTotals();
            return;
        }
        btn = e.target.closest('.remove-section');
        if (btn) {
            var card = btn.closest('.builder-section');
            card.querySelector('.present').value = '';
            card.hidden = true;
            refreshTotals();
        }
    });
    form.addEventListener('input', function (e) {
        var tr = e.target.closest('tr[data-field-row]');
        if (tr) refreshRow(tr);
        if (e.target.matches('.field-label, .section-title')) refreshTotals();
    });
    form.addEventListener('change', function (e) {
        var tr = e.target.closest('tr[data-field-row]');
        if (tr) refreshRow(tr);
        if (e.target.matches('.field-type, .section-type')) refreshTotals();
    });

    list.querySelectorAll('tr[data-field-row]').forEach(refreshRow);
    refreshTotals();
})();
