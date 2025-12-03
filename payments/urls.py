from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.status, name='payments-status'),
    path('webhook/', views.webhook, name='payments-webhook'),
]

