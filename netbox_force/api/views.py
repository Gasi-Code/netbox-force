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

_ESCALATION_DAYS = 30


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

        if secret:
            provided = (
                request.headers.get('X-NetBox-Force-Secret', '')
                or request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
            )
            if not hmac.compare_digest(secret, provided):
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

        if new_status == 'green':
            final_status = 'green'
            first_warned = None
        elif new_status == 'yellow':
            if old_status != 'yellow' or pvm.first_warned is None:
                first_warned = now
            else:
                first_warned = pvm.first_warned

            if first_warned and (now - first_warned) > timedelta(days=_ESCALATION_DAYS):
                final_status = 'red'
            else:
                final_status = 'yellow'
        else:
            final_status = 'red'
            first_warned = pvm.first_warned if pvm.first_warned else now

        PatchVM.objects.filter(pk=pvm.pk).update(
            patch_status=final_status,
            first_warned=first_warned,
            last_checked=now,
            update_details=output,
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
                'last_checked': now.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
