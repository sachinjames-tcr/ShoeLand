def wishlist_context(request):
    """Makes the wishlist icon count and product-id set available in every template."""
    if request.user.is_authenticated:
        ids = set(request.user.wishlist_items.values_list("product_id", flat=True))
    else:
        ids = set()
    return {"wishlist_total_items": len(ids), "wishlist_ids": ids}
