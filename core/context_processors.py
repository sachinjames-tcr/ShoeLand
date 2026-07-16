from django.conf import settings


def site_context(request):
    """Makes site-wide data (site name, nav categories/brands) available in every template."""
    from products.models import Category, Brand

    return {
        "SITE_NAME": settings.SITE_NAME,
        "nav_categories": Category.objects.filter(is_active=True)[:11],
        "nav_brands": Brand.objects.filter(is_active=True)[:10],
    }
