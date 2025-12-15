from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse
import requests
import concurrent.futures

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from payments.models import Payment


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

# Dashboard page (user-only)
@login_required
def dashboard(request):
    user = request.user
    # Recent payments (last 5)
    recent = Payment.objects.filter(user=user).order_by('-created_at')[:5]

    # Aggregates
    stats_qs = Payment.objects.filter(user=user)
    agg = stats_qs.aggregate(
        total_spent=Sum('amount'),
        avg_amount=Avg('amount'),
        total_count=Count('id'),
    )
    total_spent = agg.get('total_spent') or 0
    avg_amount = agg.get('avg_amount') or 0
    total_count = agg.get('total_count') or 0

    success_count = stats_qs.filter(status='success').count()
    failed_count = stats_qs.filter(status='failed').count()
    pending_count = stats_qs.filter(status='pending').count()

    success_rate = (success_count / total_count * 100) if total_count else 0

    context = {
        'total_spent': total_spent,
        'avg_amount': avg_amount,
        'total_count': total_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'success_rate': round(success_rate, 1),
        'recent_payments': recent,
    }
    return render(request, 'frontend/dashboard.html', context)


def market_prices(request):
    """Return cached market prices (coins + USD->KES rate). Cached for 5 minutes."""
    try:
        coins = cache.get('coins')
        rate = cache.get('usd_kes_rate')
    except Exception:
        coins = None
        rate = None

    if not coins or not rate:
        # Fetch list of currencies
        try:
            coins_res = requests.get("https://api.coinbase.com/v2/currencies", timeout=10).json()
            all_coins = [c for c in coins_res.get('data', []) if not c.get('details') or c['details'].get('type') == 'crypto']
        except Exception:
            all_coins = []

        # Fetch forex rate
        try:
            rate_res = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=KES", timeout=10).json()
            rate = rate_res.get('rates', {}).get('KES', 150)
        except Exception:
            rate = 150

        # Helper to fetch a single coin price
        def get_price(coin_id):
            try:
                r = requests.get(f"https://api.coinbase.com/v2/prices/{coin_id}-USD/spot", timeout=8).json()
                usd = float(r.get('data', {}).get('amount', 0) or 0)
                return usd
            except Exception:
                return 0

        coins_list = []
        # Parallel fetch prices
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(get_price, c['id']): c for c in all_coins}
            for fut in concurrent.futures.as_completed(futures):
                c = futures[fut]
                try:
                    usd = fut.result()
                except Exception:
                    usd = 0
                kes = max(1, round(usd * rate))
                coins_list.append({
                    'id': c.get('id'),
                    'name': c.get('name'),
                    'usd': usd,
                    'kes': kes,
                    'wallet': c.get('id'),
                    'image': f"https://static.coinbase.com/icons/{c.get('id')}.png"
                })

        coins = coins_list
        try:
            cache.set('coins', coins, 300)
            cache.set('usd_kes_rate', rate, 300)
        except Exception:
            pass

    return JsonResponse({'coins': coins, 'rate': rate})
