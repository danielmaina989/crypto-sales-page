from django.contrib import admin
from django.http import HttpResponse
import csv
from .models import Payment, PaymentAccessLog


class PaymentAccessLogInline(admin.TabularInline):
    model = PaymentAccessLog
    fields = ('created_at', 'user', 'username', 'action', 'ip_address', 'note')
    readonly_fields = ('created_at', 'user', 'username', 'action', 'ip_address', 'user_agent', 'note')
    extra = 0
    can_delete = False
    show_change_link = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'checkout_request_id', 'mpesa_receipt_number', 'created_at')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('checkout_request_id', 'mpesa_receipt_number', 'user__username')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
    inlines = [PaymentAccessLogInline]


def export_access_logs_csv(modeladmin, request, queryset):
    """Admin action to export selected PaymentAccessLog entries as CSV."""
    fieldnames = ['id', 'payment_id', 'user', 'username', 'action', 'ip_address', 'user_agent', 'note', 'created_at']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=payment_access_logs.csv'
    writer = csv.writer(response)
    writer.writerow(fieldnames)
    for obj in queryset:
        writer.writerow([
            obj.id,
            obj.payment_id,
            obj.user.get_username() if obj.user else '',
            obj.username or '',
            obj.action,
            obj.ip_address or '',
            (obj.user_agent or '')[:200],
            (obj.note or '')[:400],
            obj.created_at.isoformat(),
        ])
    return response


@admin.register(PaymentAccessLog)
class PaymentAccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'user', 'username', 'action', 'ip_address', 'created_at')
    readonly_fields = ('payment', 'user', 'username', 'action', 'ip_address', 'user_agent', 'note', 'created_at')
    search_fields = ('payment__id', 'user__username', 'username', 'ip_address')
    list_filter = ('action', 'created_at')
    ordering = ('-created_at',)
    actions = [export_access_logs_csv]
