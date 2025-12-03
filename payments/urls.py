from django.urls import path
from .views.callback import mpesa_callback
from .views import status, webhook
from .views.initiate import initiate_payment

urlpatterns = [
    path('status/', status, name='payments-status'),
    path('webhook/', webhook, name='payments-webhook'),
    path('mpesa/callback/', mpesa_callback, name='mpesa-callback'),
    path('initiate/', initiate_payment, name='payments-initiate'),
]
