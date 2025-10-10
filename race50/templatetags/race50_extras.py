from django import template

register = template.Library()

@register.filter(name="format_ms")
def format_ms(ms):
    """
    Format milliseconds as M:SS.mmm
    Safely handles None or non-ints.
    """
    try:
        ms = int(ms)
    except (TypeError, ValueError):
        return ""  # or return ms

    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis  = ms % 1000
    return f"{minutes}:{seconds:02d}.{millis:03d}"