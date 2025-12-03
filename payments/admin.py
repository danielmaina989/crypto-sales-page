from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'amount', 'status', 'created_at')
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    search_fields = ('reference', 'status')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
