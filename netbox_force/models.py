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

    # --- General ---
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

    # --- Ticket Reference ---
    ticket_pattern = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Ticket pattern',
        help_text=(
            'Regex pattern for required ticket references '
            '(e.g. JIRA-\\d+ or #\\d+). Leave empty to disable.'
        ),
    )

    # --- Change Window ---
    change_window_enabled = models.BooleanField(
        default=False,
        verbose_name='Enable change window',
    )
    change_window_start = models.TimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Window start time',
    )
    change_window_end = models.TimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Window end time',
    )
    change_window_weekdays = models.CharField(
        max_length=20,
        blank=True,
        default='1,2,3,4,5',
        verbose_name='Allowed weekdays',
        help_text='Comma-separated ISO weekday numbers (1=Monday, 7=Sunday)',
    )

    # --- Audit Log ---
    audit_log_enabled = models.BooleanField(
        default=False,
        verbose_name='Enable audit log',
    )
    audit_log_retention_days = models.PositiveIntegerField(
        default=90,
        verbose_name='Audit log retention (days)',
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
        with ForceSettings._cache_lock:
            ForceSettings._cached_instance = None
            ForceSettings._cache_timestamp = 0

    def delete(self, *args, **kwargs):
        pass  # Singleton must not be deleted

    @classmethod
    def get_settings(cls):
        """
        Returns plugin settings (cached, thread-safe).
        Falls back to None if the DB is unavailable.
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
        if not self.exempt_users:
            return []
        return [u.strip() for u in self.exempt_users.splitlines() if u.strip()]

    def get_blacklisted_phrases_list(self):
        if not self.blacklisted_phrases:
            return []
        return [p.strip().lower() for p in self.blacklisted_phrases.splitlines() if p.strip()]

    def get_extra_exempt_models_list(self):
        if not self.extra_exempt_models:
            return []
        return [m.strip() for m in self.extra_exempt_models.splitlines() if m.strip()]

    def get_allowed_weekdays(self):
        if not self.change_window_weekdays:
            return []
        try:
            return [int(d.strip()) for d in self.change_window_weekdays.split(',') if d.strip()]
        except ValueError:
            return []


# =============================================================================
# VALIDATION RULES
# =============================================================================

class ValidationRule(models.Model):
    """
    Configurable validation rules for naming conventions and required fields.
    Each rule targets a specific model + field combination.
    """
    RULE_TYPE_CHOICES = [
        ('naming', 'Naming Convention'),
        ('required', 'Required Field'),
    ]

    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        verbose_name='Rule type',
    )
    model_label = models.CharField(
        max_length=100,
        verbose_name='Model',
        help_text='Format: app.model (e.g. dcim.device)',
    )
    field_name = models.CharField(
        max_length=100,
        verbose_name='Field name',
        help_text='The model field to validate (e.g. name, description, tenant)',
    )
    regex_pattern = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='Regex pattern',
        help_text='Only for naming rules. The value must match this pattern.',
    )
    error_message = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='Custom error message',
        help_text='Shown to the user when validation fails. Leave empty for default.',
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name='Enabled',
    )
    created = models.DateTimeField(auto_now_add=True)

    # Cache for rules
    _rules_cache = None
    _rules_cache_timestamp = 0
    _RULES_CACHE_TTL = 30
    _rules_cache_lock = threading.Lock()

    class Meta:
        verbose_name = 'Validation Rule'
        verbose_name_plural = 'Validation Rules'
        unique_together = ['rule_type', 'model_label', 'field_name']
        ordering = ['model_label', 'field_name']

    def __str__(self):
        return f"{self.get_rule_type_display()}: {self.model_label}.{self.field_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._invalidate_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._invalidate_cache()

    @classmethod
    def _invalidate_cache(cls):
        with cls._rules_cache_lock:
            cls._rules_cache = None
            cls._rules_cache_timestamp = 0

    @classmethod
    def get_active_rules(cls):
        """Returns all active rules (cached, thread-safe)."""
        now = time.time()
        with cls._rules_cache_lock:
            if (cls._rules_cache is not None
                    and (now - cls._rules_cache_timestamp) < cls._RULES_CACHE_TTL):
                return cls._rules_cache

            try:
                rules = list(cls.objects.filter(enabled=True))
            except (OperationalError, ProgrammingError):
                return []

            cls._rules_cache = rules
            cls._rules_cache_timestamp = now
            return rules

    @classmethod
    def get_rules_for_model(cls, model_label, rule_type=None):
        """Returns active rules for a specific model."""
        rules = cls.get_active_rules()
        if rule_type:
            return [r for r in rules if r.model_label == model_label and r.rule_type == rule_type]
        return [r for r in rules if r.model_label == model_label]


# =============================================================================
# AUDIT LOG
# =============================================================================

class Violation(models.Model):
    """
    Audit log entry for blocked changes.
    Records every enforcement action for compliance tracking.
    """
    REASON_CHOICES = [
        ('missing_changelog', 'Missing Changelog'),
        ('too_short', 'Changelog Too Short'),
        ('blacklisted', 'Blacklisted Phrase'),
        ('ticket_missing', 'Missing Ticket Reference'),
        ('naming_violation', 'Naming Convention Violation'),
        ('required_field', 'Required Field Missing'),
        ('change_window', 'Outside Change Window'),
    ]

    ACTION_CHOICES = [
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    username = models.CharField(max_length=150, db_index=True)
    model_label = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200, blank=True, default='')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, db_index=True)
    message = models.TextField(blank=True, default='')
    attempted_comment = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Violation'
        verbose_name_plural = 'Violations'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} | {self.username} | {self.reason}"
