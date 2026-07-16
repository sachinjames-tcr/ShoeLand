from .cart import get_cart


def cart_context(request):
    """Makes the mini-cart (icon count + subtotal) available in every template."""
    cart = get_cart(request)
    return {
        "cart_total_items": cart.total_items,
        "cart_subtotal": cart.subtotal,
    }
