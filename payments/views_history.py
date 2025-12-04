from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from payments.models import Payment

@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'frontend/payments_history.html', {'payments': payments})

