/**
 * widget_images.js
 * Handles copy-to-clipboard and delete confirmation for the Widget Images page.
 * CSP-safe: no inline event handlers.
 */
(function () {
    'use strict';

    var config = document.getElementById('widget-images-config');
    var copiedText = config ? (config.dataset.copied || 'Copied!') : 'Copied!';

    // ── Copy-to-clipboard ────────────────────────────────────────────────────
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-copy-target]');
        if (!btn) return;

        var targetId = btn.getAttribute('data-copy-target');
        var input = document.getElementById(targetId);
        if (!input) return;

        // Modern Clipboard API (HTTPS / localhost)
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(input.value).then(function () {
                _flashCopied(btn);
            }).catch(function () {
                _fallbackCopy(input, btn);
            });
        } else {
            _fallbackCopy(input, btn);
        }
    });

    function _fallbackCopy(input, btn) {
        input.select();
        try {
            document.execCommand('copy');
            _flashCopied(btn);
        } catch (err) { /* ignore */ }
    }

    function _flashCopied(btn) {
        var icon = btn.querySelector('i');
        var orig = icon ? icon.className : '';
        if (icon) icon.className = 'mdi mdi-check';
        btn.disabled = true;

        setTimeout(function () {
            if (icon) icon.className = orig;
            btn.disabled = false;
        }, 1500);
    }

    // ── Delete confirmation ───────────────────────────────────────────────────
    document.addEventListener('submit', function (e) {
        var form = e.target.closest('.widget-image-delete-form');
        if (!form) return;

        var msg = form.dataset.confirm || 'Delete this image?';
        if (!window.confirm(msg)) {
            e.preventDefault();
        }
    });
}());
