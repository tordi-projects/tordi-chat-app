from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Conversation, Message

User = get_user_model()

TYPING_CACHE_TIMEOUT = 3  # seconds


def _typing_cache_key(conversation_id, user_id):
    return f'typing:{conversation_id}:{user_id}'


def _serialize_message(message):
    return {
        'id': message.id,
        'text': message.text,
        'sender_id': message.sender_id,
        'timestamp': message.timestamp.strftime('%H:%M'),
        'attachment_url': message.attachment.url if message.attachment else None,
        'attachment_kind': message.attachment_kind(),
    }


@login_required
def inbox_view(request):
    request.user.touch()

    conversations = list(request.user.conversations.all().order_by('-created_at'))
    for conversation in conversations:
        conversation.other = conversation.other_participant(request.user)
        conversation.last = conversation.last_message()

    query = request.GET.get('q', '').strip()
    search_results = []
    if query:
        search_results = User.objects.filter(
            Q(phone_number__icontains=query) | Q(full_name__icontains=query)
        ).exclude(id=request.user.id)[:20]

    return render(request, 'chat/inbox.html', {
        'conversations': conversations,
        'search_results': search_results,
        'query': query,
    })


@login_required
def start_conversation(request, user_id):
    other = get_object_or_404(User, id=user_id)
    conversation = (
        Conversation.objects.filter(is_group=False, participants=request.user)
        .filter(participants=other)
        .first()
    )
    if not conversation:
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.add(request.user, other)
    return redirect('chat_room', conversation_id=conversation.id)


@login_required
def chat_room_view(request, conversation_id):
    request.user.touch()

    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    conversation.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

    chat_messages = list(conversation.messages.select_related('sender').all())
    other = conversation.other_participant(request.user)
    last_message_id = chat_messages[-1].id if chat_messages else 0

    return render(request, 'chat/room.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,
        'other': other,
        'last_message_id': last_message_id,
    })


@login_required
def poll_messages(request, conversation_id):
    """
    Polled every couple of seconds by the room page. Returns any messages
    newer than `after`, plus whether the other participant is currently
    typing or online. This replaces the old WebSocket push so the app
    runs on plain WSGI hosting (e.g. PythonAnywhere) with no extra
    services required.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    request.user.touch()

    after_id = request.GET.get('after', '0')
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    new_messages = conversation.messages.filter(id__gt=after_id).select_related('sender')
    new_messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

    other = conversation.other_participant(request.user)
    other_typing = bool(other) and bool(cache.get(_typing_cache_key(conversation_id, other.id)))
    other_online = bool(other) and other.is_recently_active()

    return JsonResponse({
        'messages': [_serialize_message(m) for m in new_messages],
        'other_typing': other_typing,
        'other_online': other_online,
        'other_status': 'online' if other_online else f'last seen {other.last_seen:%b %d, %H:%M}' if other and other.last_seen else 'offline',
    })


@login_required
@require_POST
def send_message_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    request.user.touch()

    text = (request.POST.get('text') or '').strip()
    if not text:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    message = Message.objects.create(conversation=conversation, sender=request.user, text=text)
    cache.delete(_typing_cache_key(conversation_id, request.user.id))

    return JsonResponse({'status': 'ok', 'message': _serialize_message(message)})


@login_required
@require_POST
def set_typing_view(request, conversation_id):
    get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    cache.set(_typing_cache_key(conversation_id, request.user.id), True, timeout=TYPING_CACHE_TIMEOUT)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def upload_attachment(request, conversation_id):
    """Handles picture/video uploads from the composer."""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    request.user.touch()

    uploaded_file = request.FILES.get('attachment')
    caption = (request.POST.get('caption') or '').strip()

    if not uploaded_file:
        return JsonResponse({'error': 'No file provided.'}, status=400)

    max_size = 25 * 1024 * 1024  # 25MB
    if uploaded_file.size > max_size:
        return JsonResponse({'error': 'File is too large (25MB max).'}, status=400)

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        text=caption,
        attachment=uploaded_file,
    )

    return JsonResponse({'status': 'ok', 'message': _serialize_message(message)})
