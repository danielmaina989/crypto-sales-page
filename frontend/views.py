from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, Avg
import requests
import concurrent.futures
import json
from django.conf import settings
from django.views.decorators.http import require_POST
from core.utils.permissions import rate_limit
import logging

logger = logging.getLogger(__name__)

from django.contrib.auth.decorators import login_required
from payments.models import Payment
from trades.models import CryptoTrade, TradeRate


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
    
    # ===== PAYMENT STATS =====
    # Recent payments (last 5)
    recent_payments = Payment.objects.filter(user=user).order_by('-created_at')[:5]

    # Payment aggregates
    payment_qs = Payment.objects.filter(user=user)
    payment_agg = payment_qs.aggregate(
        total_spent=Sum('amount'),
        avg_amount=Avg('amount'),
        total_count=Count('id'),
    )
    payment_total_spent = payment_agg.get('total_spent') or 0
    payment_avg_amount = payment_agg.get('avg_amount') or 0
    payment_total_count = payment_agg.get('total_count') or 0

    payment_success = payment_qs.filter(status='success').count()
    payment_failed = payment_qs.filter(status='failed').count()
    payment_pending = payment_qs.filter(status='pending').count()

    payment_success_rate = (payment_success / payment_total_count * 100) if payment_total_count else 0

    # ===== BUY TRADES STATS =====
    buy_trades = CryptoTrade.objects.filter(user=user, trade_type='buy')
    buy_agg = buy_trades.aggregate(
        total_kes=Sum('amount_kes'),
        total_crypto=Sum('amount_crypto'),
        total_count=Count('id'),
    )
    buy_total_kes = buy_agg.get('total_kes') or 0
    buy_total_crypto = buy_agg.get('total_crypto') or 0
    buy_total_count = buy_agg.get('total_count') or 0
    
    buy_completed = buy_trades.filter(status='completed').count()
    buy_pending = buy_trades.filter(status__in=['pending', 'payment_confirmed', 'awaiting_payment']).count()
    
    buy_completion_rate = (buy_completed / buy_total_count * 100) if buy_total_count else 0
    
    # Get crypto coins holdings
    crypto_holdings = buy_trades.filter(status='completed').values('coin').annotate(
        total_held=Sum('amount_crypto')
    ).order_by('-total_held')[:5]
    
    # Recent buy trades (last 3)
    recent_buys = buy_trades.order_by('-created_at')[:3]

    # ===== SELL TRADES STATS =====
    sell_trades = CryptoTrade.objects.filter(user=user, trade_type='sell')
    sell_agg = sell_trades.aggregate(
        total_kes=Sum('amount_kes'),
        total_crypto=Sum('amount_crypto'),
        total_count=Count('id'),
    )
    sell_total_kes = sell_agg.get('total_kes') or 0
    sell_total_crypto = sell_agg.get('total_crypto') or 0
    sell_total_count = sell_agg.get('total_count') or 0
    
    sell_completed = sell_trades.filter(status='completed').count()
    sell_pending = sell_trades.filter(status__in=['pending', 'deposit_confirmed', 'awaiting_deposit']).count()
    
    sell_completion_rate = (sell_completed / sell_total_count * 100) if sell_total_count else 0
    
    # Recent sell trades (last 3)
    recent_sells = sell_trades.order_by('-created_at')[:3]

    context = {
        # Payment stats
        'payment_total_spent': payment_total_spent,
        'payment_avg_amount': payment_avg_amount,
        'payment_total_count': payment_total_count,
        'payment_success_count': payment_success,
        'payment_failed_count': payment_failed,
        'payment_pending_count': payment_pending,
        'payment_success_rate': round(payment_success_rate, 1),
        'recent_payments': recent_payments,
        
        # Buy trades stats
        'buy_total_kes': buy_total_kes,
        'buy_total_crypto': buy_total_crypto,
        'buy_total_count': buy_total_count,
        'buy_completed': buy_completed,
        'buy_pending': buy_pending,
        'buy_completion_rate': round(buy_completion_rate, 1),
        'crypto_holdings': list(crypto_holdings),
        'recent_buys': recent_buys,
        
        # Sell trades stats
        'sell_total_kes': sell_total_kes,
        'sell_total_crypto': sell_total_crypto,
        'sell_total_count': sell_total_count,
        'sell_completed': sell_completed,
        'sell_pending': sell_pending,
        'sell_completion_rate': round(sell_completion_rate, 1),
        'recent_sells': recent_sells,
    }
    return render(request, 'frontend/dashboard.html', context)


def detect_intent(message: str) -> str:
    """Simple intent classifier based on keyword matching.
    Returns a string tag such as 'payment', 'balance', 'trading', or 'unknown'.
    """
    msg = message.lower()
    
    # Trading-related questions
    if any(word in msg for word in ('buy', 'sell', 'trade', 'crypto', 'bitcoin', 'ethereum', 'eth', 'btc', 'coin', 'exchange', 'rate', 'price', 'spread')):
        return 'trading'
    
    # Payment-related questions
    if any(word in msg for word in ('pay', 'payment', 'mpesa', 'deposit', 'transfer', 'send money')):
        return 'payment'
    
    # Balance/wallet questions
    if any(word in msg for word in ('balance', 'wallet', 'how much', 'amount', 'own', 'have', 'holdings')):
        return 'balance'
    
    return 'unknown'


@require_POST
@rate_limit('chat', limit=20, period=60)
def chat_api(request):
    """Simple chat endpoint used by front‑end widget.

    Phase 5 additions:
    * rate-limited using the existing decorator
    * logs detected intent + chosen response handler
    * respects AI_FALLBACK_ENABLED feature flag
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
        message = payload.get('message', '')
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    intent = detect_intent(message)
    logger.info('chat_api: received message intent=%s', intent)

    # dispatch logic
    reply = None
    if intent == 'trading':
        reply = "Great! You can buy crypto on our Buy page at /buy/ using MPESA, or sell your crypto at /sell/. We offer BTC, ETH, USDT, and USDC with competitive rates. Would you like help with anything specific?"
    elif intent == 'payment':
        reply = "To buy crypto with MPESA, visit the /buy/ page. We'll send you an MPESA STK prompt on your phone. To receive MPESA from selling crypto, use the /sell/ page."
    elif intent == 'balance':
        reply = "You can view your crypto holdings and trading history on the /trades/ dashboard. Your portfolio tracks all completed buy and sell transactions."
    else:
        reply = "I can help with trading, payments, and account questions. Try asking about: 'How do I buy crypto?', 'What is the BTC rate?', or 'How do I sell crypto?'"

    return JsonResponse({'reply': reply, 'intent': intent})


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


# === Trading Pages ===

@login_required
@login_required
def buy(request):
    """Buy crypto page (MPESA → Crypto)"""
    rates = TradeRate.objects.filter(is_active=True).order_by('coin')
    context = {
        'rates': rates,
        'page_title': 'Buy Crypto',
    }
    return render(request, 'frontend/buy.html', context)


@login_required
def sell(request):
    """Sell crypto page (Crypto → MPESA)"""
    # Get all active rates
    rates = TradeRate.objects.filter(is_active=True).order_by('coin')
    
    # Get completed buy trades for this user to show only owned cryptos
    owned_cryptos = CryptoTrade.objects.filter(
        user=request.user, 
        trade_type='buy',
        status='completed'
    ).values_list('coin', flat=True).distinct()
    
    context = {
        'rates': rates,
        'owned_cryptos': list(owned_cryptos),  # Convert to list for template
        'page_title': 'Sell Crypto',
    }
    return render(request, 'frontend/sell.html', context)


@login_required
def trades(request):
    """Trade history dashboard"""
    user_trades = CryptoTrade.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate stats
    agg = user_trades.aggregate(
        total_kes=Sum('amount_kes'),
        total_trades=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        pending=Count('id', filter=Q(status__in=['pending', 'awaiting_deposit', 'payment_confirmed', 'deposit_confirmed'])),
    )
    
    buy_trades = user_trades.filter(trade_type='buy')
    sell_trades = user_trades.filter(trade_type='sell')
    
    context = {
        'trades': user_trades[:50],  # Show latest 50
        'total_kes_traded': agg.get('total_kes') or 0,
        'total_trades': agg.get('total_trades') or 0,
        'completed_trades': agg.get('completed') or 0,
        'pending_trades': agg.get('pending') or 0,
        'buy_count': buy_trades.count(),
        'sell_count': sell_trades.count(),
        'page_title': 'Trade History',
    }
    return render(request, 'frontend/trades.html', context)
