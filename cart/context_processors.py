from .cart import Cart


def cart(request):
    """Make the cart available in all templates"""
    return {'cart': Cart(request)}

