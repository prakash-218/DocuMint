// Lightweight column chart for the dashboard (no chart library needed).
// Reads [{label, full_label, revenue}] from data-series on .col-chart elements.
(function () {
    function niceStep(max, ticks) {
        var raw = max / ticks;
        var mag = Math.pow(10, Math.floor(Math.log10(raw)));
        var norm = raw / mag;
        var step = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10;
        return step * mag;
    }

    // en-IN gives Indian grouping for rupees (₹20,63,000; compact ₹20.6L)
    function formatters(currency) {
        var locale = currency === 'INR' ? 'en-IN' : undefined;
        try {
            return {
                full: new Intl.NumberFormat(locale, { style: 'currency', currency: currency }),
                short: new Intl.NumberFormat(locale, { style: 'currency', currency: currency, notation: 'compact', maximumFractionDigits: 1 })
            };
        } catch (e) {
            var plain = new Intl.NumberFormat();
            return { full: plain, short: plain };
        }
    }

    function el(tag, cls, text) {
        var node = document.createElement(tag);
        if (cls) node.className = cls;
        if (text !== undefined) node.textContent = text;   // labels are data: never innerHTML
        return node;
    }

    function render(root) {
        var series;
        try { series = JSON.parse(root.getAttribute('data-series') || '[]'); } catch (e) { return; }
        if (!series.length) return;
        var fmt = formatters(root.getAttribute('data-currency') || 'USD');
        var money = fmt.full;
        var compact = function (n) { return fmt.short.format(n); };

        var max = Math.max.apply(null, series.map(function (p) { return p.revenue; }));
        var step = max > 0 ? niceStep(max, 4) : 1;
        var top = max > 0 ? Math.ceil(max / step) * step : 4;

        var axis = el('div', 'col-chart-axis');
        var plot = el('div', 'col-chart-plot');
        for (var v = 0; v <= top + 1e-9; v += step) {
            var pct = (v / top) * 100;
            var tick = el('span', null, compact(v));
            tick.style.bottom = pct + '%';
            axis.appendChild(tick);
            if (v > 0) {
                var line = el('div', 'col-chart-grid');
                line.style.bottom = pct + '%';
                plot.appendChild(line);
            }
        }

        var bars = el('div', 'col-chart-bars');
        var tooltip = el('div', 'chart-tooltip');
        var labels = el('div', 'col-chart-labels');
        var current = series.length - 1;

        series.forEach(function (point, i) {
            var col = el('div', 'col-chart-col');
            col.tabIndex = 0;
            col.setAttribute('aria-label', point.full_label + ': ' + money.format(point.revenue));
            var bar = el('div', 'col-chart-bar');
            bar.style.height = point.revenue > 0 ? (point.revenue / top) * 100 + '%' : '0';
            if (point.revenue <= 0) bar.style.minHeight = '0';
            col.appendChild(bar);
            bars.appendChild(col);

            // Label every other month on narrow screens to avoid collisions; always label the latest
            var label = el('span', null, point.label);
            if ((current - i) % 2 === 1) label.className = 'hide-narrow';
            labels.appendChild(label);

            function show() {
                tooltip.textContent = '';
                tooltip.appendChild(el('strong', null, money.format(point.revenue)));
                tooltip.appendChild(document.createTextNode(point.full_label));
                var plotBox = plot.getBoundingClientRect();
                var colBox = col.getBoundingClientRect();
                var barTop = colBox.bottom - colBox.height * Math.max(point.revenue / top, 0);
                tooltip.style.left = (colBox.left - plotBox.left + colBox.width / 2) + 'px';
                tooltip.style.top = (barTop - plotBox.top) + 'px';
                tooltip.classList.add('visible');
            }
            function hide() { tooltip.classList.remove('visible'); }
            col.addEventListener('pointerenter', show);
            col.addEventListener('pointerleave', hide);
            col.addEventListener('focus', show);
            col.addEventListener('blur', hide);
        });

        plot.appendChild(bars);
        plot.appendChild(tooltip);
        root.textContent = '';
        root.appendChild(axis);
        root.appendChild(plot);
        root.insertAdjacentElement('afterend', labels);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.col-chart[data-series]').forEach(render);
    });
})();
