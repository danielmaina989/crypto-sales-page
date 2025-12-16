from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import redirect
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
    actions = ['admin_download_receipt']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/download-receipt/', self.admin_site.admin_view(self.download_receipt_view), name='payments_payment_download_receipt'),
        ]
        return custom_urls + urls

    def download_receipt_view(self, request, object_id, *args, **kwargs):
        """Redirect to the public download view which includes access checks/decorators."""
        try:
            obj = self.get_object(request, object_id)
            if not obj:
                self.message_user(request, 'Payment not found', level='error')
                return redirect('..')
            # redirect to payments:receipt_download (route defined in payments.urls)
            return redirect(f'/payments/receipt/{obj.id}/download/')
        except Exception as e:
            self.message_user(request, f'Error preparing receipt: {e}', level='error')
            return redirect('..')

    def admin_download_receipt(self, request, queryset):
        # If multiple selected, only allow single for direct download; otherwise export links
        if queryset.count() == 1:
            obj = queryset.first()
            return redirect(f'/payments/receipt/{obj.id}/download/')
        # Otherwise, create a zipped collection or CSV listing — for simplicity export CSV of selected receipt links
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=payment_receipts_links.csv'
        writer = csv.writer(response)
        writer.writerow(['id', 'download_url'])
        for p in queryset:
            writer.writerow([p.id, f'{request.scheme}://{request.get_host()}/payments/receipt/{p.id}/download/'])
        return response

    admin_download_receipt.short_description = 'Download receipt for selected payment (or get links)'


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
