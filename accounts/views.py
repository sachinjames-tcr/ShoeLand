from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import AddressForm, LoginForm, ProfileUpdateForm, RegisterForm, StyledPasswordChangeForm
from .models import Address, Profile


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data["email"]
            user.save()
            Profile.objects.create(user=user, phone=form.cleaned_data.get("phone", ""))
            login(request, user)
            from cart.cart import merge_session_cart_into_db
            merge_session_cart_into_db(request, user)
            messages.success(request, f"Welcome to Shoeland, {user.first_name}! Your account has been created.")
            return redirect("core:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


class ShoelandLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        from cart.cart import merge_session_cart_into_db
        merge_session_cart_into_db(self.request, self.request.user)
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)
        messages.success(self.request, f"Welcome back, {self.request.user.first_name or self.request.user.username}!")
        return response


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("core:home")


@login_required
def dashboard(request):
    from orders.models import Order

    recent_orders = Order.objects.filter(user=request.user).order_by("-created_at")[:5]
    context = {
        "recent_orders": recent_orders,
        "total_orders": Order.objects.filter(user=request.user).count(),
        "addresses": request.user.addresses.all()[:3],
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:my_profile")
    else:
        form = ProfileUpdateForm(
            instance=profile,
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
            },
        )

    return render(request, "accounts/my_profile.html", {"form": form, "profile": profile})


@login_required
def change_password(request):
    if request.method == "POST":
        form = StyledPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("accounts:my_profile")
    else:
        form = StyledPasswordChangeForm(user=request.user)

    return render(request, "accounts/change_password.html", {"form": form})


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "accounts/address_list.html", {"addresses": addresses})


@login_required
def address_add(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully.")
            return redirect("accounts:address_list")
    else:
        form = AddressForm()
    return render(request, "accounts/address_form.html", {"form": form, "title": "Add Address"})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect("accounts:address_list")
    else:
        form = AddressForm(instance=address)
    return render(request, "accounts/address_form.html", {"form": form, "title": "Edit Address"})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.delete()
        messages.success(request, "Address deleted.")
    return redirect("accounts:address_list")
