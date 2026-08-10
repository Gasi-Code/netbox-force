import hmac
import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import ForceSettings, PatchVM

logger = logging.getLogger(__name__)

_STATE_MAP = {
    'OK': 'green',
    'WARN': 'yellow',
    'WARNING': 'yellow',
    'CRIT': 'red',
    'CRITICAL': 'red',
    'UNKNOWN': 'yellow',
}

_DEFAULT_ESCALATION_DAYS = 30


def _secrets_match(expected, provided):
    """Constant-time comparison that tolerates non-ASCII secrets."""
    return hmac.compare_digest(expected.encode('utf-8'), provided.encode('utf-8'))


class CheckmkWebhookView(APIView):
    """
    Receives CheckMK system-update notifications and maps them to PatchVM
    patch_status values.

    Expected JSON payload:
        {
            "host_name": "server01.example.com",
            "state":     "OK" | "WARN" | "CRIT",
            "output":    "5 packages pending: ..."   // optional raw text
        }

    Authentication: Authorization: Bearer <checkmk_webhook_secret>
    or X-NetBox-Force-Secret: <checkmk_webhook_secret>
    (secret configured in NetBox Force plugin settings)
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        settings_obj = ForceSettings.get_settings()
        secret = getattr(settings_obj, 'checkmk_webhook_secret', '') if settings_obj else ''

        # Fail closed: an unconfigured secret must not leave the endpoint open,
        # since it can write patch status for any VM.
        if not secret:
            logger.warning('CheckMK webhook: rejected request — no secret configured')
            return Response(
                {'error': 'Webhook secret is not configured in NetBox Force settings'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        provided = (
            request.headers.get('X-NetBox-Force-Secret', '')
            or request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
        )
        if not _secrets_match(secret, provided):
            logger.warning('CheckMK webhook: rejected request — invalid secret')
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        host_name = (data.get('host_name') or '').strip()
        checkmk_state = (data.get('state') or '').upper().strip()
        output = data.get('output', '')

        if not host_name:
            return Response({'error': 'Missing host_name'}, status=status.HTTP_400_BAD_REQUEST)

        new_status = _STATE_MAP.get(checkmk_state)
        if new_status is None:
            return Response(
                {'error': f'Unknown state "{checkmk_state}". Valid: {sorted(_STATE_MAP)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pvm = (
            PatchVM.objects.filter(fqdn__iexact=host_name).first()
            or PatchVM.objects.filter(vm__name__iexact=host_name).first()
        )
        if pvm is None:
            return Response(
                {'error': f'No PatchVM found for host_name "{host_name}"'},
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()
        old_status = pvm.patch_status
        escalation_days = (
            getattr(settings_obj, 'checkmk_escalation_days', _DEFAULT_ESCALATION_DAYS)
            if settings_obj else _DEFAULT_ESCALATION_DAYS
        )

        # first_warned marks the start of an ongoing WARNING period. It survives
        # repeated WARN reports (so the clock keeps running) and is cleared by
        # both OK and a genuine CRIT — a CRIT is its own reason for red and must
        # not be mistaken for an age-based escalation later on.
        if new_status == 'green':
            final_status = 'green'
            first_warned = None
        elif new_status == 'red':
            final_status = 'red'
            first_warned = None
        else:
            first_warned = pvm.first_warned or now
            escalated = (
                escalation_days > 0
                and (now - first_warned) >= timedelta(days=escalation_days)
            )
            final_status = 'red' if escalated else 'yellow'

        PatchVM.objects.filter(pk=pvm.pk).update(
            patch_status=final_status,
            first_warned=first_warned,
            last_checked=now,
            update_details=output,
            updated=now,
        )

        logger.info(
            'CheckMK webhook: host=%s state=%s → patch_status=%s (was %s)',
            host_name, checkmk_state, final_status, old_status,
        )

        return Response(
            {
                'host_name': host_name,
                'checkmk_state': checkmk_state,
                'patch_status': final_status,
                'previous_status': old_status,
                'escalated': final_status == 'red' and new_status == 'yellow',
                'warned_since': first_warned.isoformat() if first_warned else None,
                'last_checked': now.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
