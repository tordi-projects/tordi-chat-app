from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EmailForm, OTPForm, PhoneNumberForm, ProfileForm
from .models import Contact, EmailOTP

User = get_user_model()


def send_otp_email(email, code):
    """
    Sends the verification code by email. Uses Django's EMAIL_BACKEND
    (settings.py) — defaults to printing to the console in dev, since no
    SMTP credentials are configured out of the box. Set EMAIL_HOST_USER /
    EMAIL_HOST_PASSWORD (see .env.example) to actually deliver mail.
    """
    subject = 'Your Tordi verification code'
    message = (
        f'Verify Your Email Address'
        f'Hello,'
        f'Thank you for creating an account with Tordi.'
        f'To complete your registration and secure your account, please verify your email address by copying the verification code below:'

        f'Your Tordi verification code is: {code}\n\n'

        f'This code expires in 10 minutes. If you did not request this, '
        f'This verification helps us confirm that this email address belongs to you and enables you to access all features of Tordi.'
        f'If you did not create an account with Tordi, please ignore this email. No further action is required.'
        f'Thank you for joining Tordi.'
        f'Best regards,'
        f'The Tordi Team'
        f'© 2026 Tordi. All rights reserved.'
    )
    send_mail(
        subject,
        message,
        django_settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('inbox')

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = EmailOTP.generate_code()
            EmailOTP.objects.create(email=email, code=code)
            send_otp_email(email, code)
            request.session['pending_email'] = email
            messages.success(request, 'We sent a verification code to your email.')
            return redirect('verify_otp')
    else:
        form = EmailForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inbox')

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if not User.objects.filter(email=email).exists():
                messages.error(request, "We couldn't find an account with that email.")
                return render(request, 'accounts/login.html', {'form': form})

            code = EmailOTP.generate_code()
            EmailOTP.objects.create(email=email, code=code)
            send_otp_email(email, code)
            request.session['pending_email'] = email
            return redirect('verify_otp')
    else:
        form = EmailForm()

    return render(request, 'accounts/login.html', {'form': form})


def verify_otp_view(request):
    email = request.session.get('pending_email')
    if not email:
        return redirect('register')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            otp = EmailOTP.objects.filter(
                email=email, code=code, is_used=False
            ).order_by('-created_at').first()

            if otp and not otp.is_expired():
                otp.is_used = True
                otp.save()

                user, _ = User.objects.get_or_create(email=email)
                user.is_verified = True
                user.last_seen = timezone.now()
                user.save()

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['pending_email']

                if not user.full_name:
                    return redirect('set_profile')
                return redirect('inbox')

            messages.error(request, 'That code is invalid or has expired.')
    else:
        form = OTPForm()

    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': email})


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


@login_required
def settings_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('settings')
    else:
        form = ProfileForm(instance=request.user)

    phone_form = PhoneNumberForm(instance=request.user)
    return render(request, 'accounts/settings.html', {'form': form, 'phone_form': phone_form})


@login_required
@require_POST
def update_phone_view(request):
    phone_form = PhoneNumberForm(request.POST, instance=request.user)
    if phone_form.is_valid():
        phone_form.save()
        messages.success(request, 'Phone number updated. People can now find you by it.')
    else:
        error = next(iter(phone_form.errors.get('phone_number', ['Invalid phone number.'])))
        messages.error(request, error)
    return redirect('settings')


@login_required
def contacts_list_view(request):
    contacts = Contact.objects.filter(owner=request.user).select_related('contact')
    return render(request, 'accounts/contacts.html', {'contacts': contacts})


@login_required
@require_POST
def add_contact_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target.id == request.user.id:
        return JsonResponse({'error': "You can't add yourself."}, status=400)
    Contact.objects.get_or_create(owner=request.user, contact=target)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def remove_contact_view(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, owner=request.user)
    contact.delete()
    return JsonResponse({'status': 'ok'})


def logout_view(request):
    if request.user.is_authenticated:
        request.user.last_seen = timezone.now()
        request.user.save(update_fields=['last_seen'])
    logout(request)
    return redirect('login')
