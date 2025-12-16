app_name = 'payments'

from django.urls import path
from .views.callback import mpesa_callback
from .views import status, webhook
from .views.initiate import initiate_payment
from .views.status_api import payment_status
from .views.simulate_callback import simulate_callback
from .views_history import payment_history, payment_detail, access_logs_api, history_timeseries, download_receipt

urlpatterns = [
    path('status/', status, name='payments-status'),
    path('webhook/', webhook, name='payments-webhook'),
    path('callback/', mpesa_callback, name='mpesa-callback'),
    path('initiate/', initiate_payment, name='payments-initiate'),
    path('status/<str:checkout_id>/', payment_status, name='payments-status-api'),
    path('simulate_callback/<str:checkout_id>/', simulate_callback, name='simulate-callback'),
    path('history/', payment_history, name='history'),
    path('history/<int:pk>/', payment_detail, name='history_detail'),
    path('history/logs/', access_logs_api, name='access_logs_api'),
    path('history/timeseries/', history_timeseries, name='history_timeseries'),
    path('receipt/<int:pk>/download/', download_receipt, name='receipt_download'),
]
