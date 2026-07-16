from django import forms

from accounts.models import Address


class CheckoutForm(forms.Form):
    """Collects billing/shipping details at checkout. Pre-fillable from a saved Address."""
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "House no, street"}))
    line2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Area, landmark (optional)"}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    postal_code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))
    country = forms.CharField(max_length=100, initial="India", widget=forms.TextInput(attrs={"class": "form-control"}))
    payment_method = forms.ChoiceField(
        choices=[("cod", "Cash on Delivery"), ("razorpay", "Pay with Razorpay"), ("stripe", "Pay with Stripe")],
        widget=forms.RadioSelect,
        initial="cod",
    )
    save_address = forms.BooleanField(required=False, initial=True, label="Save this address for future orders")


class CouponForm(forms.Form):
    code = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter coupon code"}),
    )
