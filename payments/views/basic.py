from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def status(request):
    return JsonResponse({'status': 'payments app is alive'})


@csrf_exempt
def webhook(request):
    # placeholder for MPESA callback handling
    if request.method == 'POST':
        return JsonResponse({'received': True})
    return JsonResponse({'error': 'invalid method'}, status=405)

