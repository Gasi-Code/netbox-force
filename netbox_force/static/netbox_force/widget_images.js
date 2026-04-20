/**
 * widget_images.js
 * - Replaces the browser-native file input with a fully translated custom widget
 * - Copy-to-clipboard for image URLs
 * - Delete confirmation
 * CSP-safe: no inline event handlers, all strings via data-* attributes.
 */
(function () {
    'use strict';

    var config = document.getElementById('widget-images-config');
    var copiedText  = config ? (config.dataset.copied     || 'Copied!')           : 'Copied!';
    var chooseText  = config ? (config.dataset.chooseFile || 'Choose file')        : 'Choose file';
    var noFileText  = config ? (config.dataset.noFile     || 'No file selected')   : 'No file selected';

    // ── Custom file input ─────────────────────────────────────────────────────
    // The browser's native <input type="file"> shows OS-locale text ("Datei auswählen",
    // "Keine ausgewählt", etc.) that cannot be changed via CSS or Django translations.
    // We hide the native input and replace it visually with a translated button + label.
    var fileInput = document.getElementById('id_file');
    if (fileInput) {
        // Hide the native input while keeping it in the DOM and form submission.
        // display:none still works — the file value is submitted normally.
        fileInput.style.display = 'none';

        // Custom "Choose file" button
        var chooseBtn = document.createElement('button');
        chooseBtn.type = 'button';
        chooseBtn.className = 'btn btn-outline-secondary btn-sm';
        chooseBtn.innerHTML = '<i class="mdi mdi-folder-open-outline"></i> ' + chooseText;
        chooseBtn.addEventListener('click', function () { fileInput.click(); });

        // Filename display
        var fileDisplay = document.createElement('span');
        fileDisplay.className = 'ms-2 small text-muted';
        fileDisplay.id = 'file-name-display';
        fileDisplay.textContent = noFileText;

        // Wrapper
        var wrapper = document.createElement('div');
        wrapper.className = 'd-flex align-items-center flex-wrap gap-1';
        wrapper.appendChild(chooseBtn);
        wrapper.appendChild(fileDisplay);

        // Insert the wrapper right after the (now hidden) native input
        fileInput.parentNode.insertBefore(wrapper, fileInput.nextSibling);

        // Update filename display whenever the user picks a file
        fileInput.addEventListener('change', function () {
            if (fileInput.files && fileInput.files.length > 0) {
                fileDisplay.textContent = fileInput.files[0].name;
                fileDisplay.className = 'ms-2 small';
            } else {
                fileDisplay.textContent = noFileText;
                fileDisplay.className = 'ms-2 small text-muted';
            }
        });
    }

    // ── Copy-to-clipboard ─────────────────────────────────────────────────────
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-copy-target]');
        if (!btn) return;

        var targetId = btn.getAttribute('data-copy-target');
        var input = document.getElementById(targetId);
        if (!input) return;

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
        try { document.execCommand('copy'); _flashCopied(btn); } catch (err) { /* ignore */ }
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
        if (!window.confirm(msg)) { e.preventDefault(); }
    });
}());
