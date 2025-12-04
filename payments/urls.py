from django.urls import path
from .views.callback import mpesa_callback
from .views import status, webhook
from .views.initiate import initiate_payment
from .views.status_api import payment_status
from .views.simulate_callback import simulate_callback
from .views_history import payment_history

urlpatterns = [
    path('status/', status, name='payments-status'),
    path('webhook/', webhook, name='payments-webhook'),
    path('callback/', mpesa_callback, name='mpesa-callback'),
    path('initiate/', initiate_payment, name='payments-initiate'),
    path('status/<str:checkout_id>/', payment_status, name='payments-status-api'),
    path('simulate_callback/<str:checkout_id>/', simulate_callback, name='payments-simulate-callback'),
    path('history/', payment_history, name='payments-history'),
]
