from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a variable key.
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
