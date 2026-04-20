/**
 * import_template_sort.js
 * Drag-and-drop row reordering for the Import Templates admin list.
 * CSP-safe: no inline event handlers, all config via data-* attributes.
 *
 * Uses native HTML5 DnD with fixes for the well-known <tr> child-element
 * flickering bug:
 *  - dragenter  → show indicator (fires once per element, not continuously)
 *  - dragover   → preventDefault only (required to allow drop)
 *  - dragleave  → hide indicator only when TRULY leaving the row
 *                 (relatedTarget check prevents child-element flicker)
 *  - drop       → reorder DOM, save via AJAX
 */
(function () {
    'use strict';

    var cfg = document.getElementById('sort-config');
    if (!cfg) return;

    var reorderUrl = cfg.dataset.reorderUrl || '';
    var csrfToken  = cfg.dataset.csrf       || '';
    var savedMsg   = cfg.dataset.saved      || 'Order saved.';
    var errorMsg   = cfg.dataset.error      || 'Error saving order.';

    var tbody = document.getElementById('sortable-template-list');
    if (!tbody || !reorderUrl) return;

    var statusEl = document.getElementById('sort-status');
    var dragSrc  = null;   // the <tr> being dragged
    var overRow  = null;   // the <tr> currently highlighted as drop target
    var dropBefore = true; // insert before or after overRow

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

    // ── Visual indicator helpers ──────────────────────────────────────────────
    function clearIndicator(row) {
        if (!row) return;
        row.style.borderTop    = '';
        row.style.borderBottom = '';
    }

    function setIndicator(row, before) {
        clearIndicator(overRow);
        overRow    = row;
        dropBefore = before;
        if (before) {
            row.style.borderTop    = '2px solid #6ea8fe';
            row.style.borderBottom = '';
        } else {
            row.style.borderTop    = '';
            row.style.borderBottom = '2px solid #6ea8fe';
        }
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
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ order: order }),
        })
        .then(function (resp) {
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            return resp.json();
        })
        .then(function (data) {
            showStatus(data.status === 'ok' ? savedMsg : errorMsg,
                       data.status !== 'ok');
        })
        .catch(function () { showStatus(errorMsg, true); });
    }

    // ── Drag event handlers ───────────────────────────────────────────────────
    function onDragStart(e) {
        dragSrc = this;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', this.dataset.pk);
        // Slight delay so the browser paints the ghost before we dim the row
        var self = this;
        setTimeout(function () { self.classList.add('opacity-50'); }, 0);
    }

    function onDragEnd() {
        this.classList.remove('opacity-50');
        clearIndicator(overRow);
        overRow = null;
        dragSrc = null;
    }

    function onDragEnter(e) {
        // Find the actual <tr> ancestor (e.target may be a <td>)
        var row = e.target.closest('tr[data-pk]');
        if (!row || row === dragSrc) return;
        e.preventDefault();

        var rect   = row.getBoundingClientRect();
        var before = e.clientY < rect.top + rect.height / 2;
        setIndicator(row, before);
    }

    function onDragOver(e) {
        // Must preventDefault to allow drop — that's all this handler needs to do.
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        // Also keep the indicator up-to-date for the top/bottom half:
        var row = e.target.closest('tr[data-pk]');
        if (!row || row === dragSrc) return;
        var rect   = row.getBoundingClientRect();
        var before = e.clientY < rect.top + rect.height / 2;
        if (row !== overRow || before !== dropBefore) {
            setIndicator(row, before);
        }
    }

    function onDragLeave(e) {
        // Ignore if we're moving to a child element of the same row
        // (this is the key fix for the <tr> child-element flicker bug)
        var row = e.target.closest('tr[data-pk]');
        if (!row) return;
        var related = e.relatedTarget;
        if (related && row.contains(related)) return;
        if (row === overRow) {
            clearIndicator(overRow);
            overRow = null;
        }
    }

    function onDrop(e) {
        e.preventDefault();
        var target = e.target.closest('tr[data-pk]');
        if (!target || !dragSrc || target === dragSrc) {
            clearIndicator(overRow);
            overRow = null;
            return;
        }

        clearIndicator(target);
        overRow = null;

        if (dropBefore) {
            tbody.insertBefore(dragSrc, target);
        } else {
            var next = target.nextSibling;
            if (next) {
                tbody.insertBefore(dragSrc, next);
            } else {
                tbody.appendChild(dragSrc);
            }
        }

        saveOrder();
    }

    // ── Attach listeners ──────────────────────────────────────────────────────
    // We attach dragenter/dragover/dragleave/drop on the tbody so that they
    // fire for ALL rows including newly reordered ones (event delegation).
    // dragstart/dragend are on each row because they need the specific row.

    tbody.addEventListener('dragenter', onDragEnter);
    tbody.addEventListener('dragover',  onDragOver);
    tbody.addEventListener('dragleave', onDragLeave);
    tbody.addEventListener('drop',      onDrop);

    tbody.querySelectorAll('tr[data-pk]').forEach(function (row) {
        row.setAttribute('draggable', 'true');
        row.addEventListener('dragstart', onDragStart);
        row.addEventListener('dragend',   onDragEnd);
    });

}());
