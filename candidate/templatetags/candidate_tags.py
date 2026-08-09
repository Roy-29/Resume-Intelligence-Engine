"""Custom template tags and filters for the candidate app."""
from django import template

register = template.Library()


@register.filter
def get_score(obj, attr):
    """Get a score attribute from the analysis object."""
    return getattr(obj, attr, 0)


@register.filter
def score_badge_bg(score):
    """Return a CSS background color based on score value."""
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 'rgba(255,255,255,0.1)'
    if score >= 80:
        return 'rgba(34,197,94,0.8)'
    elif score >= 60:
        return 'rgba(59,130,246,0.8)'
    elif score >= 40:
        return 'rgba(245,158,11,0.8)'
    else:
        return 'rgba(239,68,68,0.8)'

