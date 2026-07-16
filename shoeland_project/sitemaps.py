from django.contrib.sitemaps import Sitemap

from products.models import Product, Category, Brand


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(status="active")

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()


class BrandSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Brand.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ["core:home", "core:about", "core:contact", "products:shop", "products:categories", "products:brands"]

    def location(self, item):
        from django.urls import reverse
        return reverse(item)
