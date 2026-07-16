from django.contrib import messages
from django.shortcuts import redirect, render

from products.models import Product

from .forms import ContactForm, NewsletterForm
from .models import Banner, InstagramPost, Testimonial


def home(request):
    context = {
        "banners": Banner.objects.filter(is_active=True),
        "featured_products": Product.objects.filter(status="active", is_featured=True)[:8],
        "best_sellers": Product.objects.filter(status="active", is_best_seller=True)[:8],
        "new_arrivals": Product.objects.filter(status="active", is_new_arrival=True)[:8],
        "trending_products": Product.objects.filter(status="active", is_trending=True)[:8],
        "limited_offers": Product.objects.filter(status="active", discount_price__isnull=False)[:4],
        "testimonials": Testimonial.objects.filter(is_active=True)[:6],
        "instagram_posts": InstagramPost.objects.all()[:6],
        "newsletter_form": NewsletterForm(),
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for reaching out! We'll get back to you within 24 hours.")
            return redirect("core:contact")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form})


def privacy_policy(request):
    return render(request, "core/privacy_policy.html")


def terms_conditions(request):
    return render(request, "core/terms_conditions.html")


def subscribe_newsletter(request):
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "You're subscribed! Watch your inbox for exclusive Shoeland offers.")
        else:
            messages.error(request, "Please enter a valid email address.")
    return redirect(request.META.get("HTTP_REFERER", "core:home"))


def custom_404(request, exception=None):
    return render(request, "404.html", status=404)
