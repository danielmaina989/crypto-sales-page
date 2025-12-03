from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

try:
    from twilio.rest import Client as TwilioClient
except Exception:
    TwilioClient = None


def notify_payment_success(payment, via=('email',)):
    """Notify stakeholders of a successful payment.

    - `via` is a tuple containing 'email' and/or 'sms'.
    - For email we use Django's email backend and render a template if available.
    - For SMS we attempt to use Twilio if credentials are present.
    """
    messages = []

    subject = f"Payment successful: {payment.amount}"
    # try to render template
    try:
        body = render_to_string('payments/email/payment_success.txt', {'payment': payment})
    except Exception:
        body = f"Payment {payment.pk} for {payment.amount} succeeded. Receipt: {payment.mpesa_receipt_number}\nUser: {payment.user}\nPhone: {payment.phone_number}"

    if 'email' in via:
        # send to the user email and a configured admin email
        recipients = []
        if getattr(payment.user, 'email', None):
            recipients.append(payment.user.email)
        admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if admin_email:
            recipients.append(admin_email)
        if recipients:
            send_mail(subject, body, admin_email or 'noreply@example.com', recipients, fail_silently=True)
            messages.append(('email', recipients))

    if 'sms' in via and TwilioClient is not None:
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
        to_number = payment.phone_number
        if account_sid and auth_token and from_number and to_number:
            try:
                client = TwilioClient(account_sid, auth_token)
                client.messages.create(body=body, from_=from_number, to=to_number)
                messages.append(('sms', to_number))
            except Exception:
                # don't raise in notification
                pass

    return messages
