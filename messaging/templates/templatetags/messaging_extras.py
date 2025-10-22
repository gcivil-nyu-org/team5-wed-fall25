from django import template
register = template.Library()

@register.filter
def other_party(thread, user):
    return thread.user_b if thread.user_a_id == user.id else thread.user_a
