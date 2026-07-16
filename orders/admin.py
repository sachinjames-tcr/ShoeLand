from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "product_sku", "price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "grand_total", "payment_method", "payment_status", "status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "user__username", "email", "phone")
    list_editable = ("status", "payment_status")
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "subtotal", "discount_amount", "shipping_charge", "tax_amount", "grand_total")
