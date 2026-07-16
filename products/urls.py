from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("shop/", views.shop, name="shop"),
    path("categories/", views.categories_list, name="categories"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path("brands/", views.brands_list, name="brands"),
    path("brand/<slug:slug>/", views.brand_detail, name="brand_detail"),
    path("search/", views.search_results, name="search_results"),
    path("search/ajax/", views.live_search_ajax, name="live_search_ajax"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("product/<slug:slug>/review/add/", views.add_review, name="add_review"),
    path("product/<slug:slug>/review/<int:review_id>/edit/", views.edit_review, name="edit_review"),
    path("product/<slug:slug>/review/<int:review_id>/delete/", views.delete_review, name="delete_review"),
]
