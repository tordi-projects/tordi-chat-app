from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import OTPForm, PhoneNumberForm, ProfileForm
from .models import OTP

User = get_user_model()


def send_otp_sms(phone_number, code):
    """
    Sends the OTP to the person's real phone — via WhatsApp or SMS through
    Twilio — if Twilio credentials are configured. Falls back to printing
    the code to the console so local development works with zero setup.

    To enable real delivery, set these environment variables before
    starting the server (see README.md for the full walkthrough):
        TWILIO_ACCOUNT_SID
        TWILIO_AUTH_TOKEN
        TWILIO_FROM_NUMBER        (for SMS)
      or
        TWILIO_USE_WHATSAPP=true
        TWILIO_WHATSAPP_FROM      (for WhatsApp)
    """
    from django.conf import settings

    body = f'Your Tordi verification code is {code}. It expires in 5 minutes.'

    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        try:
            from twilio.rest import Client
        except ImportError:
            print('[Tordi] Twilio credentials are set but the "twilio" package '
                  'is not installed. Run: pip install twilio')
            print(f'[Tordi] OTP for {phone_number}: {code}')
            return

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            if settings.TWILIO_USE_WHATSAPP:
                client.messages.create(
                    body=body,
                    from_=f'whatsapp:{settings.TWILIO_WHATSAPP_FROM}',
                    to=f'whatsapp:{phone_number}',
                )
            else:
                client.messages.create(
                    body=body,
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=phone_number,
                )
            print(f'[Tordi] OTP sent to {phone_number} via '
                  f'{"WhatsApp" if settings.TWILIO_USE_WHATSAPP else "SMS"}.')
            return
        except Exception as exc:
            # Don't crash registration if the SMS/WhatsApp send fails —
            # fall back to console so the person can still test the flow.
            print(f'[Tordi] Twilio send failed ({exc}); printing code instead.')

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
                user.last_seen = timezone.now()
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
        # Push last_seen safely into the past so they read as "offline"
        # immediately, rather than waiting out the online-activity window.
        request.user.last_seen = timezone.now() - timedelta(seconds=request.user.ONLINE_THRESHOLD_SECONDS + 5)
        request.user.save(update_fields=['last_seen'])
    logout(request)
    return redirect('login')
