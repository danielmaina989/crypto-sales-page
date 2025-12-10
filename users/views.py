from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm


def profile(request):
    # For web flows, redirect profile to the dashboard page if the client prefers HTML
    # Check Accept header: browsers typically include 'text/html'. API/test clients often don't.
    accept = request.headers.get('accept', '')
    prefers_html = 'text/html' in accept
    # request.is_ajax() was removed in Django 5; check the X-Requested-With header instead
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'GET' and prefers_html and not is_ajax:
        return redirect('dashboard')
    # Fallback JSON response for API checks and tests
    return JsonResponse({'status': 'users app alive'})


def register(request):
    """Simple user registration view for development/demo purposes.
    On successful registration the user is logged in and redirected to the dashboard.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in
            login(request, user)
            # Redirect to dashboard (LOGIN_REDIRECT_URL could also be used)
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})
