from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def parse_markdown(value):
    if not isinstance(value, str):
        return value
    value = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', value)
    value = value.replace('\n', '<br><br>')
    return mark_safe(value)

@register.filter
def clean_key(value):
    return str(value).replace('_', ' ').replace('-', ' ').capitalize()
@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)
@register.filter
def split_by_comma(value):
    return [item.strip() for item in value.split(',')] if value else []
