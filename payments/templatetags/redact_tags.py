from django import template

register = template.Library()

@register.filter
def redact(value, visible=4):
    """Redact a string value leaving the last `visible` characters visible.

    Example:
        {{ 'ABCDEF'|redact }}       -> '**CDEF' (default visible=4)
        {{ '0712345678'|redact:4 }} -> '******5678'
    """
    try:
        s = str(value)
    except Exception:
        return ''
    if not s:
        return ''
    try:
        visible = int(visible)
    except Exception:
        visible = 4
    if visible < 0:
        visible = 0
    if len(s) <= visible:
        return '*' * len(s)
    masked = '*' * (len(s) - visible) + s[-visible:]
    return masked

