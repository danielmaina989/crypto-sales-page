from django import template
import locale

register = template.Library()

@register.filter
def format_kes(value):
    """Format a numeric value as KES with thousand separators.
    Falls back to simple formatting if locale is unavailable.
    Usage: {{ value|format_kes }}
    """
    try:
        # Try to use en_US locale for grouping if available
        locale.setlocale(locale.LC_ALL, '')
    except Exception:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except Exception:
            pass
    try:
        v = float(value)
        # use grouping with thousands separator
        formatted = f"{v:,.0f}"
        return f"KES {formatted}"
    except Exception:
        return f"KES {value}"

