from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


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
