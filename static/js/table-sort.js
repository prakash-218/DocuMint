

(function() {
    'use strict';

    
    function parseCellValue(cell) {
        const text = cell.textContent.trim();
        
        
        const currencyMatch = text.replace(/[$,]/g, '').match(/^[\d.]+$/);
        if (currencyMatch) {
            return parseFloat(currencyMatch[0]);
        }
        
        
        const dateMatch = text.match(/^\d{4}-\d{2}-\d{2}/);
        if (dateMatch) {
            return new Date(text);
        }
        
        
        const numberMatch = text.match(/^[\d.]+$/);
        if (numberMatch) {
            return parseFloat(text);
        }
        
        
        return text.toLowerCase();
    }

    
    function compareValues(a, b, ascending) {
        
        if (a === null || a === undefined || a === 'N/A' || a === '') {
            return 1;
        }
        if (b === null || b === undefined || b === 'N/A' || b === '') {
            return -1;
        }
        
        
        if (a instanceof Date && b instanceof Date) {
            return ascending ? a - b : b - a;
        }
        
        
        if (typeof a === 'number' && typeof b === 'number') {
            return ascending ? a - b : b - a;
        }
        
        
        if (a < b) return ascending ? -1 : 1;
        if (a > b) return ascending ? 1 : -1;
        return 0;
    }

    
    function sortTable(table, columnIndex, ascending) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        
        rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[columnIndex];
            const cellB = rowB.cells[columnIndex];
            
            if (!cellA || !cellB) return 0;
            
            const valueA = parseCellValue(cellA);
            const valueB = parseCellValue(cellB);
            
            return compareValues(valueA, valueB, ascending);
        });
        
        
        rows.forEach(row => tbody.removeChild(row));
        
        
        rows.forEach(row => tbody.appendChild(row));
        
        
        updateStripedRows(tbody);
    }

    
    function updateStripedRows(tbody) {
        const rows = tbody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            if (index % 2 === 0) {
                row.style.backgroundColor = '#151515';
            } else {
                row.style.backgroundColor = 'transparent';
            }
        });
    }

    
    function createSortIndicator(ascending) {
        const indicator = document.createElement('span');
        indicator.className = 'sort-indicator';
        
        
        if (typeof lucide !== 'undefined') {
            const iconName = ascending ? 'arrow-up' : 'arrow-down';
            indicator.innerHTML = `<i data-lucide="${iconName}" class="sort-icon"></i>`;
            
            setTimeout(() => {
                if (lucide && lucide.createIcons) {
                    lucide.createIcons();
                }
            }, 0);
        } else {
            
            indicator.textContent = ascending ? '↑' : '↓';
        }
        
        indicator.style.marginLeft = '8px';
        indicator.style.display = 'inline-flex';
        indicator.style.alignItems = 'center';
        return indicator;
    }
    
    
    function addSortableIndicator(header) {
        
        if (header.querySelector('.sortable-indicator')) {
            return;
        }
        
        const indicator = document.createElement('span');
        indicator.className = 'sortable-indicator';
        
        
        if (typeof lucide !== 'undefined') {
            indicator.innerHTML = `<i data-lucide="arrow-up-down" class="sort-icon"></i>`;
            
            setTimeout(() => {
                if (lucide && lucide.createIcons) {
                    lucide.createIcons();
                }
            }, 0);
        } else {
            
            indicator.textContent = '⇅';
        }
        
        indicator.style.marginLeft = '8px';
        indicator.style.display = 'inline-flex';
        indicator.style.alignItems = 'center';
        indicator.style.opacity = '0.4';
        indicator.style.transition = 'opacity 0.16s cubic-bezier(0.16, 1, 0.3, 1)';
        header.appendChild(indicator);
    }

    
    function clearSortIndicators(table) {
        const headers = table.querySelectorAll('thead th');
        headers.forEach(header => {
            const existing = header.querySelector('.sort-indicator');
            if (existing) {
                existing.remove();
            }
            header.classList.remove('sort-asc', 'sort-desc');
            
            header.style.backgroundColor = 'transparent';
        });
    }

    
    function initTableSort(table) {
        const headers = table.querySelectorAll('thead th');
        
        headers.forEach((header, index) => {
            
            const headerText = header.textContent.trim();
            if (headerText === 'Actions' || headerText === 'Action') {
                return;
            }
            
            
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            header.style.position = 'relative';
            header.style.transition = 'background-color 0.16s cubic-bezier(0.16, 1, 0.3, 1)';
            
            
            addSortableIndicator(header);
            
            
            header.addEventListener('mouseenter', function() {
                if (!header.classList.contains('sort-asc') && !header.classList.contains('sort-desc')) {
                    header.style.backgroundColor = 'rgba(155, 134, 255, 0.05)';
                    const sortableIndicator = header.querySelector('.sortable-indicator');
                    if (sortableIndicator) {
                        sortableIndicator.style.opacity = '0.7';
                    }
                }
            });
            
            header.addEventListener('mouseleave', function() {
                if (!header.classList.contains('sort-asc') && !header.classList.contains('sort-desc')) {
                    header.style.backgroundColor = 'transparent';
                    const sortableIndicator = header.querySelector('.sortable-indicator');
                    if (sortableIndicator) {
                        sortableIndicator.style.opacity = '0.4';
                    }
                }
            });
            
            
            header.addEventListener('click', function() {
                
                const isAscending = header.classList.contains('sort-asc');
                const isDescending = header.classList.contains('sort-desc');
                
                
                clearSortIndicators(table);
                
                
                const sortableIndicator = header.querySelector('.sortable-indicator');
                if (sortableIndicator) {
                    sortableIndicator.remove();
                }
                
                
                let newAscending;
                if (!isAscending && !isDescending) {
                    
                    newAscending = true;
                } else if (isAscending) {
                    
                    newAscending = false;
                } else {
                    
                    
                    addSortableIndicator(header);
                    updateStripedRows(table.querySelector('tbody'));
                    return;
                }
                
                
                sortTable(table, index, newAscending);
                
                
                header.classList.add(newAscending ? 'sort-asc' : 'sort-desc');
                header.appendChild(createSortIndicator(newAscending));
                
                
                header.style.backgroundColor = 'rgba(155, 134, 255, 0.1)';
            });
        });
    }

    
    function initAllTables() {
        
        const tables = document.querySelectorAll('table.table, table.list-table');
        
        tables.forEach(table => {
            
            const tbody = table.querySelector('tbody');
            if (!tbody || tbody.querySelectorAll('tr').length === 0) {
                return;
            }
            
            initTableSort(table);
        });
    }

    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllTables);
    } else {
        initAllTables();
    }
})();

