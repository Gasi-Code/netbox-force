from django.urls import path

from . import views

urlpatterns = [
    path('webhook-receiver/', views.CheckmkWebhookView.as_view(), name='checkmk_webhook'),
]
