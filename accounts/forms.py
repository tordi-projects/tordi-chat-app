from django import forms

from .models import User


class EmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'class': 'form-input',
            'autofocus': True,
        })
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class OTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '6-digit code',
            'class': 'form-input otp-input',
            'autofocus': True,
        })
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'about', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your name'}),
            'about': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'About'}),
        }


class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+234 801 234 5678',
            }),
        }

    def clean_phone_number(self):
        raw = (self.cleaned_data.get('phone_number') or '').strip().replace(' ', '')
        if not raw:
            return None  # allow clearing the field
        if not raw.startswith('+'):
            raise forms.ValidationError('Include the country code, e.g. +234...')

        existing = User.objects.filter(phone_number=raw)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('This phone number is already linked to another account.')
        return raw
