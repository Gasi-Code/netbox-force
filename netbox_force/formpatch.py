"""
Add NetBox's changelog message field to the single-object delete dialog.

NetBox records a free-form message per change in ObjectChange.message and
collects it through ChangelogMessageMixin, which its edit, bulk edit, bulk
import and bulk delete forms carry. ConfirmationForm — the form behind a single
object's delete dialog — does not, so a single deletion can neither record a
reason nor be held to one.

The templates already provide for it: templates/htmx/delete_form.html and
templates/generic/bulk_delete.html both render the field when the form exposes
it. Adding it to ConfirmationForm.base_fields is therefore enough; no NetBox
template is overridden or copied.

The field is declared exactly as NetBox declares it, so it renders and behaves
like the one on every other form.
"""

import logging

logger = logging.getLogger('netbox.plugins.netbox_force')

FIELD_NAME = 'changelog_message'


def _confirmation_form():
    try:
        from utilities.forms import ConfirmationForm
        return ConfirmationForm
    except ImportError:
        from netbox.forms import ConfirmationForm
        return ConfirmationForm


def install_delete_changelog_field():
    """
    Returns True when the field was added, False when it was already present or
    could not be added. Never raises — a NetBox release that renames or moves
    ConfirmationForm must not keep the plugin from loading.
    """
    try:
        from django import forms

        form_class = _confirmation_form()

        if FIELD_NAME in form_class.base_fields:
            return False  # NetBox provides it already

        # Same declaration as netbox/forms/mixins.py ChangelogMessageMixin, so
        # the rendered field matches the one on every other NetBox form.
        form_class.base_fields[FIELD_NAME] = forms.CharField(
            required=False,
            max_length=200,
        )
        logger.debug('netbox_force: added %s to %s',
                     FIELD_NAME, form_class.__name__)
        return True

    except Exception as exc:
        logger.warning(
            'netbox_force: could not add the changelog field to the delete '
            'dialog, single deletions cannot be enforced: %s', exc
        )
        return False
