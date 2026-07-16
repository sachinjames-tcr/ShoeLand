"""
Unified cart engine.

Logged-in users: cart is persisted in the database (Cart / CartItem models),
so it survives across devices and sessions.

Guests: cart is stored in the session as a simple {product_id: quantity} dict,
and is merged into the database cart automatically the moment they log in.
"""
from decimal import Decimal

from products.models import Product
from .models import Cart as DBCart, CartItem as DBCartItem

SESSION_KEY = "cart"


class SessionCart:
    """Cart backend for anonymous users, backed by the session."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[SESSION_KEY] = cart
        self.cart = cart

    def save(self):
        self.session.modified = True

    def add(self, product, quantity=1):
        pid = str(product.id)
        entry = self.cart.get(pid, {"quantity": 0, "saved_for_later": False})
        entry["quantity"] = entry["quantity"] + quantity
        self.cart[pid] = entry
        self.save()

    def update(self, product, quantity):
        pid = str(product.id)
        if pid in self.cart:
            self.cart[pid]["quantity"] = max(1, quantity)
            self.save()

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def toggle_save_for_later(self, product, saved=True):
        pid = str(product.id)
        if pid in self.cart:
            self.cart[pid]["saved_for_later"] = saved
            self.save()

    def clear(self):
        self.session[SESSION_KEY] = {}
        self.save()

    def get_items(self):
        """Returns a list of dicts: {product, quantity, total_price, saved_for_later}."""
        items = []
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}
        for pid, entry in self.cart.items():
            product = product_map.get(pid)
            if not product:
                continue
            items.append({
                "product": product,
                "quantity": entry["quantity"],
                "saved_for_later": entry.get("saved_for_later", False),
                "total_price": product.current_price * entry["quantity"],
            })
        return items

    @property
    def active_items(self):
        return [i for i in self.get_items() if not i["saved_for_later"]]

    @property
    def saved_items(self):
        return [i for i in self.get_items() if i["saved_for_later"]]

    @property
    def subtotal(self):
        return sum((i["total_price"] for i in self.active_items), Decimal("0.00"))

    @property
    def total_items(self):
        return sum(i["quantity"] for i in self.active_items)


class DatabaseCart:
    """Cart backend for authenticated users, backed by Cart / CartItem models."""

    def __init__(self, request):
        self.user = request.user
        self.db_cart, _ = DBCart.objects.get_or_create(user=self.user)

    def add(self, product, quantity=1):
        item, created = DBCartItem.objects.get_or_create(cart=self.db_cart, product=product, defaults={"quantity": quantity})
        if not created:
            item.quantity += quantity
            item.save()

    def update(self, product, quantity):
        DBCartItem.objects.filter(cart=self.db_cart, product=product).update(quantity=max(1, quantity))

    def remove(self, product):
        DBCartItem.objects.filter(cart=self.db_cart, product=product).delete()

    def toggle_save_for_later(self, product, saved=True):
        DBCartItem.objects.filter(cart=self.db_cart, product=product).update(saved_for_later=saved)

    def clear(self):
        self.db_cart.items.all().delete()

    def get_items(self):
        items = []
        for item in self.db_cart.items.select_related("product").all():
            items.append({
                "product": item.product,
                "quantity": item.quantity,
                "saved_for_later": item.saved_for_later,
                "total_price": item.total_price,
                "db_item_id": item.id,
            })
        return items

    @property
    def active_items(self):
        return [i for i in self.get_items() if not i["saved_for_later"]]

    @property
    def saved_items(self):
        return [i for i in self.get_items() if i["saved_for_later"]]

    @property
    def subtotal(self):
        return sum((i["total_price"] for i in self.active_items), Decimal("0.00"))

    @property
    def total_items(self):
        return sum(i["quantity"] for i in self.active_items)


def get_cart(request):
    """Returns the appropriate cart backend depending on auth status."""
    if request.user.is_authenticated:
        return DatabaseCart(request)
    return SessionCart(request)


def merge_session_cart_into_db(request, user):
    """Called on login/registration to merge a guest's session cart into their DB cart."""
    session_cart = request.session.get(SESSION_KEY)
    if not session_cart:
        return
    db_cart, _ = DBCart.objects.get_or_create(user=user)
    for pid, entry in session_cart.items():
        try:
            product = Product.objects.get(id=pid)
        except Product.DoesNotExist:
            continue
        item, created = DBCartItem.objects.get_or_create(cart=db_cart, product=product, defaults={"quantity": entry["quantity"]})
        if not created:
            item.quantity += entry["quantity"]
            item.save()
    request.session[SESSION_KEY] = {}
    request.session.modified = True
