from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from .cart import get_cart


def _totals(cart):
    subtotal = cart.subtotal
    shipping = Decimal("0.00") if subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD)) or subtotal == 0 else Decimal(str(settings.SHIPPING_FLAT_RATE))
    tax = (subtotal * Decimal(str(settings.TAX_PERCENT)) / Decimal("100")).quantize(Decimal("0.01"))
    grand_total = subtotal + shipping + tax
    return {
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
    }


def view_cart(request):
    cart = get_cart(request)
    context = {
        "cart_items": cart.active_items,
        "saved_items": cart.saved_items,
        **_totals(cart),
    }
    return render(request, "cart/cart.html", context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, status="active")
    quantity = int(request.POST.get("quantity", 1) or 1)
    cart = get_cart(request)
    cart.add(product, quantity)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": f"{product.name} added to cart.",
            "cart_total_items": cart.total_items,
            "cart_subtotal": str(cart.subtotal),
        })

    messages.success(request, f"{product.name} added to your cart.")
    return redirect(request.META.get("HTTP_REFERER", "cart:view_cart"))


def update_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            cart.remove(product)
        else:
            cart.update(product, quantity)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        totals = _totals(cart)
        return JsonResponse({
            "success": True,
            "cart_total_items": cart.total_items,
            **{k: str(v) for k, v in totals.items()},
        })

    return redirect("cart:view_cart")


def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart.remove(product)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "cart_total_items": cart.total_items})

    messages.info(request, f"{product.name} removed from your cart.")
    return redirect("cart:view_cart")


def save_for_later(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart.toggle_save_for_later(product, saved=True)
    messages.info(request, f"{product.name} saved for later.")
    return redirect("cart:view_cart")


def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart.toggle_save_for_later(product, saved=False)
    messages.success(request, f"{product.name} moved back to your cart.")
    return redirect("cart:view_cart")
