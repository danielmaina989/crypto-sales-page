from django.db import models
from django.conf import settings
from django.utils import timezone


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=13)
    account_ref = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    error_code = models.CharField(max_length=50, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    callback_raw_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["checkout_request_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.amount} - {self.status}"


# --- Audit log for access to sensitive payment details ---
class PaymentAccessLog(models.Model):
    """Record when a user (or system actor) views a Payment's sensitive details.

    This is intentionally simple: it stores a reference to the Payment, the
    actor (optional, null for anonymous/system), IP address, user agent and a
    short action/note. Use this for auditing access to `callback_raw_data` and
    other sensitive fields.
    """

    ACTION_CHOICES = [
        ("view", "View"),
        ("export", "Export"),
        ("delete", "Delete"),
        ("other", "Other"),
    ]

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="access_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default="view")
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["payment"]), models.Index(fields=["user"])]

    def __str__(self):
        who = self.username or (self.user.get_username() if self.user else "anonymous")
        return f"{who} {self.action} payment:{self.payment_id} at {self.created_at.isoformat()}"
