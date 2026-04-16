from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views import View

from .forms import ForceSettingsForm
from .models import ForceSettings


class ForceSettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Settings page for the NetBox Force plugin."""

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        settings = ForceSettings.get_settings()
        if settings is None:
            settings = ForceSettings(pk=1)
        form = ForceSettingsForm(instance=settings)
        return render(request, 'netbox_force/settings.html', {
            'form': form,
            'settings': settings,
        })

    def post(self, request):
        settings = ForceSettings.get_settings()
        if settings is None:
            settings = ForceSettings(pk=1)
        form = ForceSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('plugins:netbox_force:settings')
        return render(request, 'netbox_force/settings.html', {
            'form': form,
            'settings': settings,
        })
