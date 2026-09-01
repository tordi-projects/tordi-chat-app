from django import forms

from .models import User


class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+234 801 234 5678',
            'class': 'form-input',
            'autofocus': True,
        })
    )

    def clean_phone_number(self):
        raw = self.cleaned_data['phone_number'].strip().replace(' ', '')
        if not raw.startswith('+'):
            raise forms.ValidationError('Include the country code, e.g. +234...')
        return raw


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
