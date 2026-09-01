from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import OTPForm, PhoneNumberForm, ProfileForm
from .models import OTP

User = get_user_model()


def send_otp_sms(phone_number, code):
    """
    Placeholder SMS gateway. Prints the code to the console so you can
    test the flow without a paid SMS provider.

    To go live, wire in a real provider here, e.g. Twilio:

        from twilio.rest import Client
        from django.conf import settings
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Your Tordi verification code is {code}",
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone_number,
        )
    """
    print(f'[Tordi] OTP for {phone_number}: {code}')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('inbox')

    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            code = OTP.generate_code()
            OTP.objects.create(phone_number=phone_number, code=code)
            send_otp_sms(phone_number, code)
            request.session['pending_phone'] = phone_number
            messages.success(request, 'We sent a verification code to your phone.')
            return redirect('verify_otp')
    else:
        form = PhoneNumberForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inbox')

    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            if not User.objects.filter(phone_number=phone_number).exists():
                messages.error(request, "We couldn't find an account with that number.")
                return render(request, 'accounts/login.html', {'form': form})

            code = OTP.generate_code()
            OTP.objects.create(phone_number=phone_number, code=code)
            send_otp_sms(phone_number, code)
            request.session['pending_phone'] = phone_number
            return redirect('verify_otp')
    else:
        form = PhoneNumberForm()

    return render(request, 'accounts/login.html', {'form': form})


def verify_otp_view(request):
    phone_number = request.session.get('pending_phone')
    if not phone_number:
        return redirect('register')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            otp = OTP.objects.filter(
                phone_number=phone_number, code=code, is_used=False
            ).order_by('-created_at').first()

            if otp and not otp.is_expired():
                otp.is_used = True
                otp.save()

                user, _ = User.objects.get_or_create(phone_number=phone_number)
                user.is_verified = True
                user.is_online = True
                user.save()

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['pending_phone']

                if not user.full_name:
                    return redirect('set_profile')
                return redirect('inbox')

            messages.error(request, 'That code is invalid or has expired.')
    else:
        form = OTPForm()

    return render(request, 'accounts/verify_otp.html', {'form': form, 'phone_number': phone_number})


def set_profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('inbox')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/set_profile.html', {'form': form})


def settings_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('settings')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/settings.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        request.user.is_online = False
        request.user.last_seen = timezone.now()
        request.user.save()
    logout(request)
    return redirect('login')
