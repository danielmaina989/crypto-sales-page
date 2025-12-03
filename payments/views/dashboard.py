from django.shortcuts import render
from payments.models import Payment


def dashboard(request):
    payments = Payment.objects.all().order_by('-created_at')[:50]
    return render(request, 'payments/dashboard.html', {'payments': payments})

