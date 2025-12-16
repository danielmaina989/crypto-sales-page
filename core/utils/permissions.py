import functools
import logging
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


def rate_limit(key_prefix, limit=10, period=60):
    """Simple rate limiter decorator using Django cache.

    Usage:
        @rate_limit('payments_initiate', limit=4, period=60)
        def view(request):
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(request, *args, **kwargs):
            # Build cache key
            ident = request.META.get('REMOTE_ADDR', 'anon')
            key = f"rl:{key_prefix}:{ident}"
            try:
                current = cache.get(key) or 0
                if current >= limit:
                    logger.warning('Rate limit exceeded for %s (key=%s)', ident, key)
                    return HttpResponseForbidden('Rate limit exceeded')
                cache.incr(key)
                # set expiry when first created
                if current == 0:
                    cache.set(key, 1, period)
            except Exception:
                # If cache not available, allow through but log
                logger.exception('Rate limiter cache failure; allowing request')
            return fn(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_or_owner_required(model_cls, lookup_field='pk', owner_field='user'):
    """Decorator to allow access only to staff or the owner of the object.

    It also logs access attempts to `PaymentAccessLog` model if present.
    Usage:
        @admin_or_owner_required(Payment, lookup_field='id')
        def payment_detail(request, id):
            ...
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # resolve object id
            lookup_val = kwargs.get(lookup_field)
            obj = get_object_or_404(model_cls, pk=lookup_val)

            # permission check
            if request.user.is_authenticated and (request.user.is_staff or getattr(obj, owner_field) == request.user):
                # log access if model exists
                try:
                    from payments.models import PaymentAccessLog
                    PaymentAccessLog.objects.create(
                        payment=obj,
                        user=request.user if request.user.is_authenticated else None,
                        action='viewed',
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                except Exception:
                    logger.exception('Failed to log payment access')
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden('Permission denied')
        return _wrapped
    return decorator
