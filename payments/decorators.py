from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from payments.models import PaymentAccessLog, Payment
from django.shortcuts import get_object_or_404


def support_required(view_func):
    """Decorator to restrict access to support/admin users.

    By default this checks `user.is_staff` or `user.is_superuser`. You can
    customize this to check group membership or a permission.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        user = request.user
        # Allow superuser or staff
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return view_func(request, *args, **kwargs)
        # Optional: check default 'view' permission for Payment model
        if user.has_perm("payments.view_payment"):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You do not have permission to view this resource.")

    return _wrapped


def audit_and_require_payment_view(param_name='pk'):
    """Decorator factory: enforces access for payment detail views and logs access.

    Usage:
        @audit_and_require_payment_view('pk')
        def payment_detail(request, pk):
            ...

    The decorator will:
    - resolve the Payment by `param_name` from kwargs
    - allow owners, staff/superusers, or users with `payments.view_payment`
    - record an access log (and unauthorized attempts)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            # get the payment id from kwargs or args
            pid = kwargs.get(param_name)
            if pid is None:
                # try to support positional args (less common)
                try:
                    # find the index of the param_name if present in the signature — fallback: first arg
                    pid = args[0]
                except Exception:
                    return HttpResponseForbidden('Missing payment identifier')

            payment = get_object_or_404(Payment, pk=pid)

            is_owner = (payment.user_id == request.user.id)
            is_staff = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
            has_perm = request.user.has_perm('payments.view_payment') if request.user.is_authenticated else False

            if not (is_owner or is_staff or has_perm):
                # log unauthorized attempt
                try:
                    PaymentAccessLog.objects.create(
                        payment=payment,
                        user=request.user if request.user.is_authenticated else None,
                        username=request.user.get_username() if request.user.is_authenticated else None,
                        action='view',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        note='unauthorized_view_attempt',
                    )
                except Exception:
                    pass
                return HttpResponseForbidden('You do not have permission to view this resource')

            # authorized -> log access
            try:
                PaymentAccessLog.objects.create(
                    payment=payment,
                    user=request.user if request.user.is_authenticated else None,
                    username=request.user.get_username() if request.user.is_authenticated else None,
                    action='view',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                )
            except Exception:
                pass

            # call the original view with same params
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
