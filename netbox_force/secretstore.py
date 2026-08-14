"""
At-rest protection for the CheckMK automation secret.

The realistic exposure for a self-hosted NetBox is a database dump that ends
up somewhere it should not — a NAS share, a backup bucket. Such a dump never
contains Django's SECRET_KEY, so encrypting with a key derived from it keeps
the secret unusable outside the running installation.

It is deliberately not a defence against an attacker who already holds both
the filesystem and the database. That case is covered by the CheckMK side:
the automation user is read-only.
"""

import base64
import hashlib
import logging

logger = logging.getLogger(__name__)

_ENC_PREFIX = 'enc:'
_RAW_PREFIX = 'raw:'


def crypto_available():
    try:
        from cryptography.fernet import Fernet  # noqa: F401
        return True
    except Exception:
        return False


# The CheckMK secret predates any other stored credential and was encrypted
# under this fixed seed. It stays the default so existing values keep decoding
# after an upgrade; new callers pass their own purpose.
DEFAULT_PURPOSE = 'checkmk'


def _fernet(purpose=DEFAULT_PURPOSE):
    from cryptography.fernet import Fernet
    from django.conf import settings

    seed = f'netbox_force.{purpose}:{settings.SECRET_KEY}'.encode('utf-8')
    key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
    return Fernet(key)


def encrypt(value, purpose=DEFAULT_PURPOSE):
    """Encode a secret for storage. Returns '' for an empty input."""
    if not value:
        return ''
    if not crypto_available():
        logger.warning(
            'netbox_force: cryptography unavailable — the %s secret is '
            'stored unencrypted', purpose
        )
        return _RAW_PREFIX + value
    try:
        token = _fernet(purpose).encrypt(value.encode('utf-8')).decode('ascii')
        return _ENC_PREFIX + token
    except Exception:
        logger.exception('netbox_force: encrypting the %s secret failed', purpose)
        return _RAW_PREFIX + value


def decrypt(stored, purpose=DEFAULT_PURPOSE):
    """
    Decode a stored secret. Values written before this scheme existed carry
    no prefix and are returned unchanged.
    """
    if not stored:
        return ''
    if stored.startswith(_RAW_PREFIX):
        return stored[len(_RAW_PREFIX):]
    if not stored.startswith(_ENC_PREFIX):
        return stored
    if not crypto_available():
        logger.error(
            'netbox_force: the %s secret is encrypted but cryptography is '
            'not installed', purpose
        )
        return ''
    try:
        return _fernet(purpose).decrypt(
            stored[len(_ENC_PREFIX):].encode('ascii')).decode('utf-8')
    except Exception:
        # Happens when SECRET_KEY changed — the secret has to be re-entered.
        logger.error(
            'netbox_force: the %s secret could not be decrypted; it was '
            'likely encrypted under a different SECRET_KEY', purpose
        )
        return ''


def is_encrypted(stored):
    return bool(stored) and stored.startswith(_ENC_PREFIX)
