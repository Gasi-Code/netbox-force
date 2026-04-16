import threading
import time

from django.db import models
from django.db.utils import OperationalError, ProgrammingError


LANGUAGE_CHOICES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
    ('es', 'Español'),
]


class ForceSettings(models.Model):
    """
    Singleton model for plugin settings.
    Only one row (pk=1) exists in the database.
    """
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='de',
        verbose_name='Language',
    )
    min_length = models.PositiveIntegerField(
        default=2,
        verbose_name='Minimum changelog length',
    )
    enforce_on_create = models.BooleanField(
        default=False,
        verbose_name='Enforce on create',
    )
    enforce_on_delete = models.BooleanField(
        default=True,
        verbose_name='Enforce on delete',
    )
    exempt_users = models.TextField(
        blank=True,
        default='',
        verbose_name='Exempt users',
        help_text='One username per line',
    )
    blacklisted_phrases = models.TextField(
        blank=True,
        default='',
        verbose_name='Blocked phrases',
        help_text=(
            'One phrase per line. Changelog entries containing any of '
            'these phrases (as whole words) will be rejected.'
        ),
    )
    extra_exempt_models = models.TextField(
        blank=True,
        default='',
        verbose_name='Exempt models',
        help_text='One model per line (format: app.model, e.g. myplugin.mymodel)',
    )

    # In-memory cache with thread safety
    _cached_instance = None
    _cache_timestamp = 0
    _CACHE_TTL = 30  # seconds
    _cache_lock = threading.Lock()

    class Meta:
        verbose_name = 'NetBox Force Settings'
        verbose_name_plural = 'NetBox Force Settings'

    def __str__(self):
        return 'NetBox Force Settings'

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)
        # Invalidate cache
        with ForceSettings._cache_lock:
            ForceSettings._cached_instance = None
            ForceSettings._cache_timestamp = 0

    def delete(self, *args, **kwargs):
        pass  # Singleton must not be deleted

    @classmethod
    def get_settings(cls):
        """
        Returns plugin settings (cached).
        Falls back to PLUGINS_CONFIG defaults if the DB is unavailable.
        """
        now = time.time()
        with cls._cache_lock:
            if (cls._cached_instance is not None
                    and (now - cls._cache_timestamp) < cls._CACHE_TTL):
                return cls._cached_instance

            try:
                obj, created = cls.objects.get_or_create(pk=1)
                if created:
                    cls._init_from_config(obj)
            except (OperationalError, ProgrammingError):
                # DB unavailable (migration not run, etc.)
                return None

            cls._cached_instance = obj
            cls._cache_timestamp = now
            return obj

    @classmethod
    def _init_from_config(cls, obj):
        """Initializes DB settings from PLUGINS_CONFIG defaults."""
        from netbox.plugins import get_plugin_config

        obj.min_length = get_plugin_config('netbox_force', 'min_length') or 2
        obj.enforce_on_create = bool(
            get_plugin_config('netbox_force', 'enforce_on_create'))
        obj.enforce_on_delete = bool(
            get_plugin_config('netbox_force', 'enforce_on_delete'))

        exempt = get_plugin_config('netbox_force', 'exempt_users') or []
        obj.exempt_users = '\n'.join(exempt) if isinstance(exempt, list) else ''

        extra = get_plugin_config('netbox_force', 'extra_exempt_models') or []
        obj.extra_exempt_models = '\n'.join(extra) if isinstance(extra, list) else ''

        obj.save()

    def get_exempt_users_list(self):
        """Returns exempt users as a list."""
        if not self.exempt_users:
            return []
        return [u.strip() for u in self.exempt_users.splitlines() if u.strip()]

    def get_blacklisted_phrases_list(self):
        """Returns blocked phrases as a lowercase list."""
        if not self.blacklisted_phrases:
            return []
        return [p.strip().lower() for p in self.blacklisted_phrases.splitlines() if p.strip()]

    def get_extra_exempt_models_list(self):
        """Returns exempt models as a list."""
        if not self.extra_exempt_models:
            return []
        return [m.strip() for m in self.extra_exempt_models.splitlines() if m.strip()]
