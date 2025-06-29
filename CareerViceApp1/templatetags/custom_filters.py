from django import template

register = template.Library()

@register.filter
def clean_key(value):
    return str(value).replace('_', ' ').replace('-', ' ').capitalize()
@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)
@register.filter
def split_by_comma(value):
    return [item.strip() for item in value.split(',')] if value else []
