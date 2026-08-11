"""
No public API endpoints.

The CheckMK integration used to expose an inbound webhook receiver here. It
was replaced by an outbound pull (see netbox_force/sync.py), which removes the
unauthenticated endpoint entirely — NetBox now only ever calls CheckMK, never
the other way around.
"""

urlpatterns = []
