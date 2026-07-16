from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("coupon/apply/", views.apply_coupon, name="apply_coupon"),
    path("coupon/remove/", views.remove_coupon, name="remove_coupon"),
    path("success/<str:order_number>/", views.order_success, name="order_success"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("<str:order_number>/", views.order_detail, name="order_detail"),
    path("<str:order_number>/cancel/", views.cancel_order, name="cancel_order"),
    path("<str:order_number>/invoice/", views.download_invoice, name="download_invoice"),
]
