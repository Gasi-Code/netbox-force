"""
Template helpers for NetBox Force.

Django's own `timesince` renders in NetBox's active locale, while every other
label on these pages comes from the plugin's own language setting. With the
two set differently that produced sentences like "5 Minuten ago". The filter
below reads the plugin language instead, and uses a compact unit form so no
preposition or plural rule is needed in any of the sixteen languages.
"""

from django import template
from django.utils import timezone

register = template.Library()

_FALLBACK = {
    'time_now': 'now',
    'unit_minute_short': 'min',
    'unit_hour_short': 'h',
    'unit_day_short': 'd',
    'unit_month_short': 'mo',
    'unit_year_short': 'y',
}


def _strings():
    try:
        from ..models import ForceSettings
        from ..ui_strings import get_all_ui_strings
        settings_obj = ForceSettings.get_settings()
        lang = getattr(settings_obj, 'language', 'en') if settings_obj else 'en'
        return get_all_ui_strings(lang)
    except Exception:
        return {}


@register.filter
def force_age(value):
    """
    Compact age of a datetime: 'now', '5 min', '3 h', '2 d', '4 mo', '1 y'.

    Returns an empty string for a missing value so templates can use it
    directly without a surrounding {% if %}.
    """
    if not value:
        return ''

    ui = _strings()

    def s(key):
        return ui.get(key) or _FALLBACK[key]

    try:
        seconds = int((timezone.now() - value).total_seconds())
    except (TypeError, ValueError):
        return ''

    # A clock skew between NetBox and the database can put a timestamp
    # slightly in the future; reporting a negative age helps no one.
    if seconds < 60:
        return s('time_now')
    if seconds < 3600:
        return f"{seconds // 60} {s('unit_minute_short')}"
    if seconds < 86400:
        return f"{seconds // 3600} {s('unit_hour_short')}"
    if seconds < 86400 * 30:
        return f"{seconds // 86400} {s('unit_day_short')}"
    if seconds < 86400 * 365:
        return f"{seconds // (86400 * 30)} {s('unit_month_short')}"
    return f"{seconds // (86400 * 365)} {s('unit_year_short')}"
