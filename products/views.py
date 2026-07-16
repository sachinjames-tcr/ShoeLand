from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm
from .models import Brand, Category, Product, Review

PRODUCTS_PER_PAGE = 12


def _apply_filters(request, queryset):
    """Shared filter/sort logic used by shop, category, brand, and search views."""
    category_slugs = request.GET.getlist("category")
    if category_slugs:
        queryset = queryset.filter(category__slug__in=category_slugs)

    brand_slugs = request.GET.getlist("brand")
    if brand_slugs:
        queryset = queryset.filter(brand__slug__in=brand_slugs)

    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    if price_min:
        queryset = queryset.filter(price__gte=price_min)
    if price_max:
        queryset = queryset.filter(price__lte=price_max)

    rating_min = request.GET.get("rating")
    if rating_min:
        queryset = queryset.filter(rating__gte=rating_min)

    availability = request.GET.get("availability")
    if availability == "in_stock":
        queryset = queryset.filter(stock__gt=0)
    elif availability == "out_of_stock":
        queryset = queryset.filter(stock=0)

    sort = request.GET.get("sort", "latest")
    sort_map = {
        "latest": "-created_at",
        "price_low": "price",
        "price_high": "-price",
        "best_selling": "-sold_count",
        "top_rated": "-rating",
    }
    queryset = queryset.order_by(sort_map.get(sort, "-created_at"))
    return queryset


def shop(request):
    products = Product.objects.filter(status="active")
    products = _apply_filters(request, products)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.filter(is_active=True),
        "brands": Brand.objects.filter(is_active=True),
        "selected_categories": request.GET.getlist("category"),
        "selected_brands": request.GET.getlist("brand"),
        "current_sort": request.GET.get("sort", "latest"),
        "page_title": "Shop All Shoes",
    }
    return render(request, "products/shop.html", context)


def categories_list(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, "products/categories.html", {"categories": categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(status="active", category=category)
    products = _apply_filters(request, products)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "category": category,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.filter(is_active=True),
        "brands": Brand.objects.filter(is_active=True),
        "selected_brands": request.GET.getlist("brand"),
        "current_sort": request.GET.get("sort", "latest"),
        "page_title": category.name,
    }
    return render(request, "products/category_detail.html", context)


def brands_list(request):
    brands = Brand.objects.filter(is_active=True)
    return render(request, "products/brands.html", {"brands": brands})


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug, is_active=True)
    products = Product.objects.filter(status="active", brand=brand)
    products = _apply_filters(request, products)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "brand": brand,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.filter(is_active=True),
        "brands": Brand.objects.filter(is_active=True),
        "current_sort": request.GET.get("sort", "latest"),
        "page_title": brand.name,
    }
    return render(request, "products/brand_detail.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category", "brand").prefetch_related("images", "reviews__user"),
        slug=slug,
    )
    related_products = Product.objects.filter(
        category=product.category, status="active"
    ).exclude(pk=product.pk)[:4]

    reviews = product.reviews.select_related("user").all()
    user_has_reviewed = (
        request.user.is_authenticated and reviews.filter(user=request.user).exists()
    )
    form = ReviewForm()

    context = {
        "product": product,
        "related_products": related_products,
        "reviews": reviews,
        "review_form": form,
        "user_has_reviewed": user_has_reviewed,
    }
    return render(request, "products/product_detail.html", context)


def search_results(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.filter(status="active")

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(brand__name__icontains=query)
        )
    else:
        products = products.none()

    products = _apply_filters(request, products)

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "query": query,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.filter(is_active=True),
        "brands": Brand.objects.filter(is_active=True),
        "current_sort": request.GET.get("sort", "latest"),
        "page_title": f'Search results for "{query}"' if query else "Search",
    }
    return render(request, "products/search_results.html", context)


def live_search_ajax(request):
    """Returns a small JSON list of matching products for the live search dropdown."""
    from django.http import JsonResponse

    query = request.GET.get("q", "").strip()
    results = []
    if len(query) >= 2:
        products = Product.objects.filter(status="active", name__icontains=query)[:6]
        for p in products:
            results.append({
                "name": p.name,
                "url": p.get_absolute_url(),
                "price": str(p.current_price),
                "image": p.images.first().image.url if p.images.exists() else "",
            })
    return JsonResponse({"results": results})


@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "You have already reviewed this product. You can edit your review below.")
        return redirect("products:product_detail", slug=slug)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            _recalculate_rating(product)
            messages.success(request, "Thank you! Your review has been posted.")
        else:
            messages.error(request, "Please correct the errors in your review.")
    return redirect("products:product_detail", slug=slug)


@login_required
def edit_review(request, slug, review_id):
    product = get_object_or_404(Product, slug=slug)
    review = get_object_or_404(Review, pk=review_id, product=product, user=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            _recalculate_rating(product)
            messages.success(request, "Your review has been updated.")
        else:
            messages.error(request, "Please correct the errors in your review.")
    return redirect("products:product_detail", slug=slug)


@login_required
def delete_review(request, slug, review_id):
    product = get_object_or_404(Product, slug=slug)
    review = get_object_or_404(Review, pk=review_id, product=product, user=request.user)
    if request.method == "POST":
        review.delete()
        _recalculate_rating(product)
        messages.success(request, "Your review has been deleted.")
    return redirect("products:product_detail", slug=slug)


def _recalculate_rating(product):
    reviews = product.reviews.all()
    count = reviews.count()
    if count:
        avg = sum(r.rating for r in reviews) / count
    else:
        avg = 0
    product.rating = round(avg, 2)
    product.rating_count = count
    product.save(update_fields=["rating", "rating_count"])
