"""Custom template tags for the candidate app."""
from django import template

register = template.Library()


@register.filter
def join(value, delimiter=', '):
    """Join a list with a delimiter."""
    if isinstance(value, (list, tuple)):
        return delimiter.join(str(v) for v in value)
    return value
