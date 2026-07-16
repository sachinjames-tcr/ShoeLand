from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import get_cart
from products.models import Product
from .models import Wishlist


@login_required
def view_wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "wishlist/wishlist.html", {"items": items})


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        added = False
    else:
        added = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "added": added,
            "wishlist_total_items": Wishlist.objects.filter(user=request.user).count(),
        })

    messages.success(request, f"{product.name} {'added to' if added else 'removed from'} your wishlist.")
    return redirect(request.META.get("HTTP_REFERER", "wishlist:view_wishlist"))


@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    messages.info(request, "Item removed from wishlist.")
    return redirect("wishlist:view_wishlist")


@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart.add(product, 1)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"{product.name} moved to your cart.")
    return redirect("wishlist:view_wishlist")
