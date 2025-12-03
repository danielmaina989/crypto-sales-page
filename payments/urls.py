from django.urls import path
from .views.callback import mpesa_callback
from .views import status, webhook
from .views.initiate import initiate_payment
from .views.status_api import payment_status

urlpatterns = [
    path('status/', status, name='payments-status'),
    path('webhook/', webhook, name='payments-webhook'),
    path('mpesa/callback/', mpesa_callback, name='mpesa-callback'),
    path('initiate/', initiate_payment, name='payments-initiate'),
    path('status/<str:checkout_id>/', payment_status, name='payments-status-api'),
]
