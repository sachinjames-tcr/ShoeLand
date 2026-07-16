from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User

from .models import Profile, Address

BOOTSTRAP_INPUT = {"class": "form-control"}


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=BOOTSTRAP_INPUT))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=BOOTSTRAP_INPUT))
    email = forms.EmailField(widget=forms.EmailInput(attrs=BOOTSTRAP_INPUT))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=BOOTSTRAP_INPUT))

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(BOOTSTRAP_INPUT)
        self.fields["password1"].widget.attrs.update(BOOTSTRAP_INPUT)
        self.fields["password2"].widget.attrs.update(BOOTSTRAP_INPUT)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({**BOOTSTRAP_INPUT, "placeholder": "Username or email"})
        self.fields["password"].widget.attrs.update(BOOTSTRAP_INPUT)


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=BOOTSTRAP_INPUT))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=BOOTSTRAP_INPUT))
    email = forms.EmailField(widget=forms.EmailInput(attrs=BOOTSTRAP_INPUT))

    class Meta:
        model = Profile
        fields = ["phone", "avatar", "date_of_birth", "gender", "newsletter_opt_in"]
        widgets = {
            "phone": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={**BOOTSTRAP_INPUT, "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "address_type", "full_name", "phone", "line1", "line2",
            "city", "state", "postal_code", "country", "is_default",
        ]
        widgets = {
            "address_type": forms.Select(attrs={"class": "form-select"}),
            "full_name": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "phone": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "line1": forms.TextInput(attrs={**BOOTSTRAP_INPUT, "placeholder": "House no, street"}),
            "line2": forms.TextInput(attrs={**BOOTSTRAP_INPUT, "placeholder": "Area, landmark (optional)"}),
            "city": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "state": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "postal_code": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "country": forms.TextInput(attrs=BOOTSTRAP_INPUT),
        }


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(BOOTSTRAP_INPUT)
