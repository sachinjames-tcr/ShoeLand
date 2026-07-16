from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.view_cart, name="view_cart"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("update/<int:product_id>/", views.update_cart_item, name="update_cart_item"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("save-for-later/<int:product_id>/", views.save_for_later, name="save_for_later"),
    path("move-to-cart/<int:product_id>/", views.move_to_cart, name="move_to_cart"),
]
