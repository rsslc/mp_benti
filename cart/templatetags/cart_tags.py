from django import template

register = template.Library()


@register.filter
def cart_quantity(cart, product_id):
    """Get the quantity of a product in the cart"""
    return cart.get_product_quantity(product_id)

