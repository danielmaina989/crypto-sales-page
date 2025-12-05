from django.shortcuts import render

def home(request):
    return render(request, 'frontend/index.html')

# Placeholder pages used by the navbar
def market(request):
    return render(request, 'frontend/market.html')

def features(request):
    return render(request, 'frontend/features.html')

def whitepapers(request):
    return render(request, 'frontend/whitepapers.html')

def about(request):
    return render(request, 'frontend/about.html')

# Dashboard page (simple placeholder for now)
def dashboard(request):
    return render(request, 'frontend/dashboard.html')
