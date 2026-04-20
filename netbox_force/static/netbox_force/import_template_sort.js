/**
 * import_template_sort.js
 * Drag-and-drop row reordering for the Import Templates admin list.
 * CSP-safe: no inline event handlers, all strings via data-* attributes.
 * Uses native HTML5 Drag and Drop API — no external dependencies.
 */
(function () {
    'use strict';

    var cfg = document.getElementById('sort-config');
    if (!cfg) return;

    var reorderUrl = cfg.dataset.reorderUrl || '';
    var savedMsg   = cfg.dataset.saved      || 'Order saved.';
    var errorMsg   = cfg.dataset.error      || 'Error saving order.';

    var tbody = document.getElementById('sortable-template-list');
    if (!tbody || !reorderUrl) return;

    var statusEl = document.getElementById('sort-status');
    var dragSrc  = null;   // the row being dragged

    // ── CSRF helper ──────────────────────────────────────────────────────────
    function getCsrf() {
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    // ── Status toast ─────────────────────────────────────────────────────────
    function showStatus(msg, isError) {
        if (!statusEl) return;
        statusEl.textContent = msg;
        statusEl.className = 'small ' + (isError ? 'text-danger' : 'text-success');
        statusEl.style.setProperty('display', 'inline', 'important');
        statusEl.style.opacity = '1';
        clearTimeout(statusEl._timer);
        statusEl._timer = setTimeout(function () {
            statusEl.style.opacity = '0';
            setTimeout(function () {
                statusEl.style.setProperty('display', 'none', 'important');
            }, 450);
        }, 2500);
    }

    // ── AJAX save ────────────────────────────────────────────────────────────
    function saveOrder() {
        var rows  = tbody.querySelectorAll('tr[data-pk]');
        var order = Array.prototype.map.call(rows, function (r) {
            return parseInt(r.dataset.pk, 10);
        });

        fetch(reorderUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrf(),
            },
            body: JSON.stringify({ order: order }),
        })
        .then(function (resp) {
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            return resp.json();
        })
        .then(function (data) {
            if (data.status === 'ok') {
                showStatus(savedMsg, false);
            } else {
                showStatus(errorMsg, true);
            }
        })
        .catch(function () {
            showStatus(errorMsg, true);
        });
    }

    // ── Drag & Drop handlers ──────────────────────────────────────────────────
    function onDragStart(e) {
        dragSrc = this;
        e.dataTransfer.effectAllowed = 'move';
        // Store PK so browsers without dataTransfer text support still work
        e.dataTransfer.setData('text/plain', this.dataset.pk);
        this.classList.add('opacity-50');
    }

    function onDragEnd() {
        this.classList.remove('opacity-50');
        // Clean up any lingering indicators
        tbody.querySelectorAll('tr').forEach(function (r) {
            r.classList.remove('drag-over-top', 'drag-over-bottom');
            r.style.borderTop    = '';
            r.style.borderBottom = '';
        });
    }

    function onDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        if (!dragSrc || dragSrc === this) return;

        // Visual indicator: insert line above or below depending on cursor position
        var rect   = this.getBoundingClientRect();
        var midY   = rect.top + rect.height / 2;
        var before = e.clientY < midY;

        tbody.querySelectorAll('tr').forEach(function (r) {
            r.style.borderTop    = '';
            r.style.borderBottom = '';
        });
        if (before) {
            this.style.borderTop = '2px solid #6ea8fe';
        } else {
            this.style.borderBottom = '2px solid #6ea8fe';
        }
        this._dropBefore = before;
    }

    function onDragLeave() {
        this.style.borderTop    = '';
        this.style.borderBottom = '';
    }

    function onDrop(e) {
        e.preventDefault();
        if (!dragSrc || dragSrc === this) return;

        var before = this._dropBefore !== false;
        if (before) {
            tbody.insertBefore(dragSrc, this);
        } else {
            // insert after this row
            var next = this.nextSibling;
            if (next) {
                tbody.insertBefore(dragSrc, next);
            } else {
                tbody.appendChild(dragSrc);
            }
        }

        this.style.borderTop    = '';
        this.style.borderBottom = '';

        saveOrder();
    }

    // ── Attach listeners to every row ────────────────────────────────────────
    function bindRow(row) {
        row.setAttribute('draggable', 'true');
        row.addEventListener('dragstart', onDragStart);
        row.addEventListener('dragend',   onDragEnd);
        row.addEventListener('dragover',  onDragOver);
        row.addEventListener('dragleave', onDragLeave);
        row.addEventListener('drop',      onDrop);
    }

    tbody.querySelectorAll('tr[data-pk]').forEach(bindRow);

}());
