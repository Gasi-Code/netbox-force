/* NetBox Force — Guide Editor
 * Handles WYSIWYG (Quill) and HTML-Code mode switching.
 * Loaded as an external static file to remain CSP-compliant.
 */
/* global Quill */
(function () {
    'use strict';

    function init() {
        if (typeof Quill === 'undefined') {
            console.error('NetBox Force: Quill.js not loaded — guide editor disabled');
            return;
        }

        // Read config values from the hidden data element in the template
        var cfg = document.getElementById('guide-editor-config');
        var confirmMsg = cfg ? cfg.getAttribute('data-confirm-switch') : 'The HTML content is a full page. Switching to WYSIWYG will lose formatting. Switch anyway?';
        var previewEmpty = cfg ? cfg.getAttribute('data-preview-empty') : 'Preview...';

        var quill = new Quill('#quill-editor', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    ['link', 'image'],
                    ['blockquote', 'code-block'],
                    [{ 'color': [] }, { 'background': [] }],
                    ['clean']
                ]
            }
        });

        var hiddenInput   = document.getElementById('id_content');
        var wysiwygPanel  = document.getElementById('wysiwyg-editor-panel');
        var htmlPanel     = document.getElementById('html-editor-panel');
        var htmlArea      = document.getElementById('html-editor-area');
        var previewFrame  = document.getElementById('preview-iframe');
        var tabWysiwyg    = document.getElementById('tab-wysiwyg');
        var tabHtml       = document.getElementById('tab-html');
        var currentMode   = 'wysiwyg';
        var previewTimer  = null;

        // --- Live preview ------------------------------------------------
        function updatePreview() {
            var content = htmlArea.value;
            if (!content.trim()) {
                previewFrame.srcdoc = '<html><body style="font-family:sans-serif;color:#888;'
                    + 'text-align:center;padding:40px;"><p>' + previewEmpty + '...</p></body></html>';
                return;
            }
            if (/^\s*<!DOCTYPE|^\s*<html/i.test(content)) {
                previewFrame.srcdoc = content;
            } else {
                previewFrame.srcdoc = '<html><head><style>body{font-family:sans-serif;'
                    + 'padding:20px;line-height:1.6;}</style></head><body>' + content + '</body></html>';
            }
        }

        htmlArea.addEventListener('input', function () {
            clearTimeout(previewTimer);
            previewTimer = setTimeout(updatePreview, 400);
        });

        // --- Tab-key support in textarea --------------------------------
        htmlArea.addEventListener('keydown', function (e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                var start = this.selectionStart;
                var end   = this.selectionEnd;
                this.value = this.value.substring(0, start) + '  ' + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 2;
            }
        });

        // --- Editor mode switching ---------------------------------------
        function switchEditor(mode) {
            if (mode === currentMode) return;

            if (mode === 'html') {
                if (currentMode === 'wysiwyg') {
                    var quillHtml = quill.root.innerHTML;
                    if (quillHtml === '<p><br></p>') quillHtml = '';
                    if (!htmlArea.value.trim()) {
                        htmlArea.value = quillHtml;
                    }
                }
                wysiwygPanel.style.display = 'none';
                htmlPanel.style.display    = '';
                tabWysiwyg.classList.remove('active');
                tabHtml.classList.add('active');
                updatePreview();
            } else {
                var htmlContent = htmlArea.value.trim();
                var isPage = /^\s*<!DOCTYPE|^\s*<html/i.test(htmlContent);
                if (isPage && !confirm(confirmMsg)) {
                    return;
                }
                if (htmlContent) {
                    quill.root.innerHTML = htmlContent;
                }
                htmlPanel.style.display    = 'none';
                wysiwygPanel.style.display = '';
                tabHtml.classList.remove('active');
                tabWysiwyg.classList.add('active');
            }
            currentMode = mode;
        }

        // Wire tab clicks via event listeners (no inline onclick needed)
        tabWysiwyg.addEventListener('click', function () { switchEditor('wysiwyg'); });
        tabHtml.addEventListener('click',    function () { switchEditor('html'); });

        // --- Load existing content into the right editor ----------------
        var existingContent = hiddenInput ? hiddenInput.value : '';
        var isFullHtml = /^\s*<!DOCTYPE|^\s*<html/i.test(existingContent);

        if (isFullHtml) {
            htmlArea.value = existingContent;
            switchEditor('html');
        } else if (existingContent) {
            quill.root.innerHTML = existingContent;
        }

        // --- Sync to hidden input on submit -----------------------------
        var form = document.getElementById('guide-form');
        if (form) {
            form.addEventListener('submit', function () {
                if (currentMode === 'html') {
                    hiddenInput.value = htmlArea.value;
                } else {
                    var html = quill.root.innerHTML;
                    if (html === '<p><br></p>') html = '';
                    hiddenInput.value = html;
                }
            });
        }
    }

    // Scripts are placed at the end of the content block, so the DOM is
    // already ready. Call init() directly — no DOMContentLoaded needed.
    init();
})();
