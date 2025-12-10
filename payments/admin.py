from django.contrib import admin
from .models import Payment, PaymentAccessLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'checkout_request_id', 'mpesa_receipt_number', 'created_at')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('checkout_request_id', 'mpesa_receipt_number', 'user__username')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)

@admin.register(PaymentAccessLog)
class PaymentAccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'user', 'username', 'action', 'ip_address', 'created_at')
    readonly_fields = ('payment', 'user', 'username', 'action', 'ip_address', 'user_agent', 'note', 'created_at')
    search_fields = ('payment__id', 'user__username', 'username', 'ip_address')
    list_filter = ('action', 'created_at')
    ordering = ('-created_at',)
