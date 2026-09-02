import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Status, StatusView
from .utils import can_view_status

User = get_user_model()

STATUS_COLORS = ['#5B4FE9', '#17C3B2', '#F97316', '#EC4899', '#0EA5E9', '#8B5CF6', '#EF4444']


@login_required
def my_status_view(request):
    my_statuses = list(request.user.statuses.filter(expires_at__gt=timezone.now()).order_by('created_at'))
    for s in my_statuses:
        s.viewer_list = User.objects.filter(id__in=s.views.values_list('viewer_id', flat=True))
    return render(request, 'status/my_status.html', {'statuses': my_statuses})


@login_required
@require_POST
def create_status_view(request):
    text = (request.POST.get('text') or '').strip()
    media = request.FILES.get('media')

    if not text and not media:
        return JsonResponse({'error': 'Add text or a photo/video first.'}, status=400)

    if media and media.size > 25 * 1024 * 1024:
        return JsonResponse({'error': 'File is too large (25MB max).'}, status=400)

    status = Status.objects.create(
        user=request.user,
        text=text,
        media=media,
        background_color=random.choice(STATUS_COLORS),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    return JsonResponse({'status': 'ok', 'id': status.id})


@login_required
@require_POST
def delete_status_view(request, status_id):
    status = get_object_or_404(Status, id=status_id, user=request.user)
    status.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def view_status(request, user_id):
    owner = get_object_or_404(User, id=user_id)

    if not can_view_status(owner, request.user):
        messages.error(request, "You don't have access to this person's status.")
        return redirect('inbox')

    statuses = list(owner.statuses.filter(expires_at__gt=timezone.now()).order_by('created_at'))
    if not statuses:
        return redirect('inbox')

    return render(request, 'status/viewer.html', {'owner': owner, 'statuses': statuses})


@login_required
@require_POST
def mark_status_viewed(request, status_id):
    status = get_object_or_404(Status, id=status_id, expires_at__gt=timezone.now())
    if not can_view_status(status.user, request.user):
        return JsonResponse({'error': 'Not allowed.'}, status=403)
    if status.user_id != request.user.id:
        StatusView.objects.get_or_create(status=status, viewer=request.user)
    return JsonResponse({'status': 'ok'})
