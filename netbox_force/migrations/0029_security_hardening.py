"""
Security hardening.

Three schema changes, each paired with the data move it needs:

* Widget image bytes move from MEDIA_ROOT into the database. NetBox serves
  MEDIA_URL without an authentication check, so every uploaded file was
  readable by anyone who knew its name — the login requirement on the serving
  view never applied to the file itself. The old files are deleted from disk as
  part of the move, because leaving them there would leave the hole open.
* The webhook secret is encrypted at rest, like the CheckMK secret and the
  Graylog token already were.
* patch_viewer_groups and hosts_failed are new fields.
"""

import logging
import os

from django.db import migrations, models

logger = logging.getLogger(__name__)


def _media_path(name):
    from django.conf import settings
    return os.path.join(settings.MEDIA_ROOT, name.replace('/', os.sep))


def widget_images_into_db(apps, schema_editor):
    """Read every stored file into its row, then remove it from disk."""
    WidgetImage = apps.get_model('netbox_force', 'WidgetImage')

    for image in WidgetImage.objects.all():
        stored_name = getattr(image, 'file', None)
        stored_name = getattr(stored_name, 'name', None) or ''
        if not stored_name:
            continue
        path = _media_path(stored_name)
        try:
            with open(path, 'rb') as handle:
                image.data = handle.read()
            image.file_size = len(image.data)
            image.save(update_fields=['data', 'file_size'])
        except OSError:
            logger.warning(
                'netbox_force: widget image %r could not be read from %s — the '
                'row is kept but the image will not render until it is '
                're-uploaded', image.name, path)
            continue
        try:
            os.remove(path)
        except OSError:
            logger.warning(
                'netbox_force: widget image %r was copied into the database '
                'but %s could not be deleted — remove it by hand, it is served '
                'without authentication', image.name, path)


def widget_images_noop_reverse(apps, schema_editor):
    """
    Nothing to undo.

    The bytes are in the database and the files are gone; recreating them under
    MEDIA_ROOT would restore the exposure this migration exists to remove.
    """
    return


def encrypt_webhook_secret(apps, schema_editor):
    """Move any plaintext webhook secret into the encrypted column."""
    from netbox_force.secretstore import encrypt

    ForceSettings = apps.get_model('netbox_force', 'ForceSettings')
    for row in ForceSettings.objects.all():
        plaintext = (getattr(row, 'webhook_secret', '') or '').strip()
        if not plaintext:
            continue
        row.webhook_secret_encrypted = encrypt(plaintext, purpose='webhook')
        row.save(update_fields=['webhook_secret_encrypted'])


def decrypt_webhook_secret(apps, schema_editor):
    """Reverse path, so the migration can be rolled back without data loss."""
    from netbox_force.secretstore import decrypt

    ForceSettings = apps.get_model('netbox_force', 'ForceSettings')
    for row in ForceSettings.objects.all():
        stored = (getattr(row, 'webhook_secret_encrypted', '') or '').strip()
        if not stored:
            continue
        row.webhook_secret = decrypt(stored, purpose='webhook')[:255]
        row.save(update_fields=['webhook_secret'])


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_force', '0028_graylog_readback'),
    ]

    operations = [
        # --- Widget images: disk → database -------------------------------
        migrations.AddField(
            model_name='widgetimage',
            name='data',
            field=models.BinaryField(default=b'', editable=False,
                                     verbose_name='File content'),
        ),
        migrations.RunPython(widget_images_into_db, widget_images_noop_reverse),
        migrations.RemoveField(
            model_name='widgetimage',
            name='file',
        ),

        # --- Webhook secret: plaintext → encrypted -------------------------
        migrations.AddField(
            model_name='forcesettings',
            name='webhook_secret_encrypted',
            field=models.TextField(
                blank=True, default='', verbose_name='Webhook secret',
                help_text='Optional HMAC-SHA256 secret. If set, adds an '
                          'X-NetBox-Force-Signature header. Stored encrypted. '
                          'Never rendered back into the form.'),
        ),
        migrations.RunPython(encrypt_webhook_secret, decrypt_webhook_secret),
        migrations.RemoveField(
            model_name='forcesettings',
            name='webhook_secret',
        ),

        # --- New settings and counters ------------------------------------
        migrations.AddField(
            model_name='forcesettings',
            name='patch_viewer_groups',
            field=models.TextField(
                blank=True, default='', verbose_name='Patch viewer groups',
                help_text='Comma-separated NetBox group names allowed to READ '
                          'the patch pages. Leave empty to let every logged-in '
                          'user read them (previous behaviour). Editor and '
                          'import groups always retain read access.'),
        ),
        migrations.AddField(
            model_name='checkmksyncrun',
            name='hosts_failed',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Hosts skipped because reconciling them raised. The '
                          'rest of the run still completed.'),
        ),
    ]
