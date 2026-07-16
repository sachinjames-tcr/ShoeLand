import io
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Address
from cart.cart import get_cart
from products.models import Coupon

from .forms import CheckoutForm, CouponForm
from .models import Order, OrderItem


def _get_coupon(request):
    code = request.session.get("coupon_code")
    if not code:
        return None
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return None
    return coupon if coupon.is_valid() else None


def _calculate_totals(cart, coupon=None):
    subtotal = cart.subtotal
    discount = coupon.calculate_discount(subtotal) if coupon and subtotal >= coupon.minimum_order_amount else Decimal("0.00")
    taxable = subtotal - discount
    shipping = Decimal("0.00") if subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD)) or subtotal == 0 else Decimal(str(settings.SHIPPING_FLAT_RATE))
    tax = (taxable * Decimal(str(settings.TAX_PERCENT)) / Decimal("100")).quantize(Decimal("0.01"))
    grand_total = taxable + shipping + tax
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
    }


@login_required
def apply_coupon(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"].strip()
            try:
                coupon = Coupon.objects.get(code__iexact=code)
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")
                return redirect("cart:view_cart")
            if not coupon.is_valid():
                messages.error(request, "This coupon has expired or reached its usage limit.")
                return redirect("cart:view_cart")
            request.session["coupon_code"] = coupon.code
            messages.success(request, f"Coupon '{coupon.code}' applied!")
    return redirect(request.META.get("HTTP_REFERER", "cart:view_cart"))


@login_required
def remove_coupon(request):
    request.session.pop("coupon_code", None)
    messages.info(request, "Coupon removed.")
    return redirect(request.META.get("HTTP_REFERER", "cart:view_cart"))


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.active_items:
        messages.warning(request, "Your cart is empty. Add some products before checking out.")
        return redirect("products:shop")

    coupon = _get_coupon(request)
    totals = _calculate_totals(cart, coupon)

    default_address = request.user.addresses.filter(is_default=True).first() or request.user.addresses.first()
    initial = {}
    if default_address:
        initial = {
            "full_name": default_address.full_name,
            "phone": default_address.phone,
            "email": request.user.email,
            "line1": default_address.line1,
            "line2": default_address.line2,
            "city": default_address.city,
            "state": default_address.state,
            "postal_code": default_address.postal_code,
            "country": default_address.country,
        }
    else:
        initial = {"email": request.user.email, "full_name": request.user.get_full_name()}

    if request.method == "POST":
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            data = form.cleaned_data

            order = Order.objects.create(
                user=request.user,
                full_name=data["full_name"],
                phone=data["phone"],
                email=data["email"],
                shipping_line1=data["line1"],
                shipping_line2=data["line2"],
                shipping_city=data["city"],
                shipping_state=data["state"],
                shipping_postal_code=data["postal_code"],
                shipping_country=data["country"],
                coupon=coupon,
                subtotal=totals["subtotal"],
                discount_amount=totals["discount"],
                shipping_charge=totals["shipping"],
                tax_amount=totals["tax"],
                grand_total=totals["grand_total"],
                payment_method=data["payment_method"],
                payment_status="paid" if data["payment_method"] in ("razorpay", "stripe") else "pending",
                status="confirmed" if data["payment_method"] in ("razorpay", "stripe") else "pending",
            )

            for item in cart.active_items:
                product = item["product"]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    price=product.current_price,
                    quantity=item["quantity"],
                )
                product.stock = max(0, product.stock - item["quantity"])
                product.sold_count += item["quantity"]
                product.save(update_fields=["stock", "sold_count"])

            if coupon:
                coupon.used_count += 1
                coupon.save(update_fields=["used_count"])

            if data.get("save_address"):
                Address.objects.create(
                    user=request.user,
                    address_type="shipping",
                    full_name=data["full_name"],
                    phone=data["phone"],
                    line1=data["line1"],
                    line2=data["line2"],
                    city=data["city"],
                    state=data["state"],
                    postal_code=data["postal_code"],
                    country=data["country"],
                    is_default=not request.user.addresses.exists(),
                )

            cart.clear()
            request.session.pop("coupon_code", None)

            messages.success(request, "Your order has been placed successfully!")
            return redirect("orders:order_success", order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    context = {
        "form": form,
        "cart_items": cart.active_items,
        "coupon": coupon,
        **totals,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, "orders/checkout.html", context)


@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_success.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == "POST" and order.is_cancellable:
        order.status = "cancelled"
        order.save(update_fields=["status"])
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=["stock"])
        messages.success(request, f"Order {order.order_number} has been cancelled.")
    else:
        messages.error(request, "This order can no longer be cancelled.")
    return redirect("orders:order_detail", order_number=order.order_number)


@login_required
def download_invoice(request, order_number):
    """Generates a simple PDF invoice for the order using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 25 * mm
    p.setFont("Helvetica-Bold", 18)
    p.drawString(20 * mm, y, "Shoeland")
    p.setFont("Helvetica", 10)
    p.drawRightString(width - 20 * mm, y, f"Invoice #{order.order_number}")
    y -= 6 * mm
    p.drawRightString(width - 20 * mm, y, order.created_at.strftime("%d %b %Y"))

    y -= 12 * mm
    p.setFont("Helvetica-Bold", 11)
    p.drawString(20 * mm, y, "Billed To:")
    p.setFont("Helvetica", 10)
    y -= 6 * mm
    for line in [order.full_name, order.shipping_line1, order.shipping_line2,
                 f"{order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}",
                 order.shipping_country, order.phone]:
        if line:
            p.drawString(20 * mm, y, line)
            y -= 5 * mm

    y -= 8 * mm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(20 * mm, y, "Item")
    p.drawString(110 * mm, y, "Qty")
    p.drawString(130 * mm, y, "Price")
    p.drawString(160 * mm, y, "Total")
    y -= 3 * mm
    p.line(20 * mm, y, width - 20 * mm, y)
    y -= 6 * mm

    p.setFont("Helvetica", 9)
    for item in order.items.all():
        p.drawString(20 * mm, y, item.product_name[:45])
        p.drawString(110 * mm, y, str(item.quantity))
        p.drawString(130 * mm, y, f"Rs. {item.price}")
        p.drawString(160 * mm, y, f"Rs. {item.total_price}")
        y -= 6 * mm
        if y < 40 * mm:
            p.showPage()
            y = height - 25 * mm

    y -= 4 * mm
    p.line(20 * mm, y, width - 20 * mm, y)
    y -= 8 * mm

    p.setFont("Helvetica", 10)
    for label, value in [
        ("Subtotal", order.subtotal),
        ("Discount", -order.discount_amount),
        ("Shipping", order.shipping_charge),
        ("Tax", order.tax_amount),
    ]:
        p.drawRightString(155 * mm, y, f"{label}:")
        p.drawRightString(width - 20 * mm, y, f"Rs. {value}")
        y -= 6 * mm

    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(155 * mm, y, "Grand Total:")
    p.drawRightString(width - 20 * mm, y, f"Rs. {order.grand_total}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"invoice_{order.order_number}.pdf")
