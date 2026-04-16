import time

from django.db import models


LANGUAGE_CHOICES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
    ('es', 'Español'),
]


class ForceSettings(models.Model):
    """
    Singleton-Model für Plugin-Einstellungen.
    Nur eine Zeile (pk=1) existiert in der Datenbank.
    """
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='de',
        verbose_name='Sprache / Language',
    )
    min_length = models.PositiveIntegerField(
        default=2,
        verbose_name='Mindestlänge Changelog',
    )
    enforce_on_create = models.BooleanField(
        default=False,
        verbose_name='Beim Erstellen erzwingen',
    )
    enforce_on_delete = models.BooleanField(
        default=True,
        verbose_name='Beim Löschen erzwingen',
    )
    exempt_users = models.TextField(
        blank=True,
        default='',
        verbose_name='Ausgenommene Benutzer',
        help_text='Ein Benutzername pro Zeile',
    )
    blacklisted_phrases = models.TextField(
        blank=True,
        default='',
        verbose_name='Gesperrte Begriffe',
        help_text='Ein Begriff pro Zeile. Changelog-Einträge die nur aus diesen Begriffen bestehen werden abgelehnt.',
    )
    extra_exempt_models = models.TextField(
        blank=True,
        default='',
        verbose_name='Ausgenommene Modelle',
        help_text='Ein Model pro Zeile (Format: app.model, z.B. myplugin.mymodel)',
    )

    # In-Memory-Cache
    _cached_instance = None
    _cache_timestamp = 0
    _CACHE_TTL = 30  # Sekunden

    class Meta:
        verbose_name = 'NetBox Force Einstellungen'
        verbose_name_plural = 'NetBox Force Einstellungen'

    def __str__(self):
        return 'NetBox Force Einstellungen'

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton erzwingen
        super().save(*args, **kwargs)
        # Cache invalidieren
        ForceSettings._cached_instance = None
        ForceSettings._cache_timestamp = 0

    def delete(self, *args, **kwargs):
        pass  # Singleton darf nicht gelöscht werden

    @classmethod
    def get_settings(cls):
        """
        Gibt die Plugin-Einstellungen zurück (gecacht).
        Fällt auf PLUGINS_CONFIG-Defaults zurück wenn DB nicht verfügbar.
        """
        now = time.time()
        if (cls._cached_instance is not None
                and (now - cls._cache_timestamp) < cls._CACHE_TTL):
            return cls._cached_instance

        try:
            obj, created = cls.objects.get_or_create(pk=1)
            if created:
                # Initialisierung aus PLUGINS_CONFIG
                cls._init_from_config(obj)
        except Exception:
            # DB nicht verfügbar (Migration nicht gelaufen o.ä.)
            return None

        cls._cached_instance = obj
        cls._cache_timestamp = now
        return obj

    @classmethod
    def _init_from_config(cls, obj):
        """Initialisiert die DB-Einstellungen aus PLUGINS_CONFIG."""
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
        """Gibt die ausgenommenen User als Liste zurück."""
        if not self.exempt_users:
            return []
        return [u.strip() for u in self.exempt_users.splitlines() if u.strip()]

    def get_blacklisted_phrases_list(self):
        """Gibt die gesperrten Begriffe als Liste zurück."""
        if not self.blacklisted_phrases:
            return []
        return [p.strip().lower() for p in self.blacklisted_phrases.splitlines() if p.strip()]

    def get_extra_exempt_models_list(self):
        """Gibt die ausgenommenen Modelle als Liste zurück."""
        if not self.extra_exempt_models:
            return []
        return [m.strip() for m in self.extra_exempt_models.splitlines() if m.strip()]
