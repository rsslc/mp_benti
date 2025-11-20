from django import template

register = template.Library()


@register.simple_tag
def get_form_value(form_data, prefix, product_id, default=''):
    """
    Get a value from form_data dictionary using a prefix and product ID.

    Usage in template:
        {% get_form_value form_data 'quantity_' product.id %}
        {% get_form_value form_data 'price_ex_gst_' product.id product.price_ex_gst %}
    """
    if form_data is None:
        return default if default else ''

    # Ensure form_data is a dictionary
    if not isinstance(form_data, dict):
        return default if default else ''

    key = f"{prefix}{product_id}"
    value = form_data.get(key)

    # Return form value if it exists, otherwise return default
    if value is not None and value != '':
        return value

    return default if default else ''


@register.filter
def add(value, arg):
    """
    Add the arg to the value, handling string concatenation.
    This is used to construct dynamic dictionary keys.

    Usage:
        {{ 'quantity_'|add:product.id }}  -> 'quantity_5'
    """
    try:
        return str(value) + str(arg)
    except (ValueError, TypeError):
        return ''
