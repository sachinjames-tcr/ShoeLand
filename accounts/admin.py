from django.contrib import admin
from .models import Profile, Address


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "gender", "newsletter_opt_in")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "address_type", "city", "state", "is_default")
    list_filter = ("address_type", "state")
    search_fields = ("user__username", "full_name", "city")
