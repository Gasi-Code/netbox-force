"""
Graylog panel on the device and virtual machine pages.

NetBox discovers `template_extensions` in this module automatically.

The panel renders from one database row and nothing else. The messages are
fetched afterwards by the browser, so a slow or dead Graylog delays a small
panel instead of the whole object page — the difference between an annoyance
and an outage of the NetBox UI.

Both `model` and `models` are set because NetBox renamed the attribute during
the 4.x line and the plugin supports 4.0 upwards. Whichever one the running
release reads, it finds a correct value.
"""

import logging

from django.utils.html import escape

logger = logging.getLogger(__name__)

try:
    from netbox.plugins import PluginTemplateExtension
    EXTENSIONS_AVAILABLE = True
except Exception:  # pragma: no cover - depends on NetBox version
    PluginTemplateExtension = object
    EXTENSIONS_AVAILABLE = False


def _ui():
    from .models import ForceSettings
    from .ui_strings import get_all_ui_strings

    settings_obj = ForceSettings.get_settings()
    language = getattr(settings_obj, 'language', 'en') if settings_obj else 'en'
    return get_all_ui_strings(language), settings_obj


class _GraylogPanel(PluginTemplateExtension):
    """Shared rendering for both object types."""

    def right_page(self):
        try:
            return self._render()
        except Exception:
            logger.debug('netbox_force: Graylog panel failed', exc_info=True)
            return ''

    def _render(self):
        obj = self.context.get('object')
        if obj is None:
            return ''

        ui, settings_obj = _ui()
        if settings_obj is None or not settings_obj.graylog_read_enabled:
            return ''

        source = self._find_source(obj)
        return self.render('netbox_force/panels/graylog_object.html', extra_context={
            'ui': ui,
            'graylog_source': source,
            'graylog_object': obj,
            'graylog_silent': (
                source.is_silent(settings_obj.graylog_silent_after_hours)
                if source else False),
            'graylog_window_hours': settings_obj.graylog_window_hours,
            'graylog_object_label': escape(str(obj)),
        })

    @staticmethod
    def _find_source(obj):
        """
        The mapped source for this object, if any.

        One indexed lookup. No API call, no matching work — the poll already
        did that.
        """
        from django.contrib.contenttypes.models import ContentType

        from .models import GraylogSource

        try:
            content_type = ContentType.objects.get_for_model(obj.__class__)
            return GraylogSource.objects.filter(
                matched_type=content_type, matched_id=obj.pk).first()
        except Exception:
            return None


class DeviceGraylogPanel(_GraylogPanel):
    model = 'dcim.device'
    models = ['dcim.device']


class VirtualMachineGraylogPanel(_GraylogPanel):
    model = 'virtualization.virtualmachine'
    models = ['virtualization.virtualmachine']


template_extensions = (
    [DeviceGraylogPanel, VirtualMachineGraylogPanel]
    if EXTENSIONS_AVAILABLE else []
)
