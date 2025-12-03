from django.shortcuts import render
from django.http import JsonResponse


def profile(request):
    return JsonResponse({'status': 'users app alive'})

