from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'checkout_request_id', 'mpesa_receipt_number', 'created_at')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('checkout_request_id', 'mpesa_receipt_number', 'user__username')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
