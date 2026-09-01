from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Conversation, Message

User = get_user_model()


@login_required
def inbox_view(request):
    conversations = list(request.user.conversations.all().order_by('-created_at'))
    # Precompute per-conversation display data here rather than in the
    # template, since Django templates can't call a method with an
    # argument (e.g. other_participant(request.user)).
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
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    conversation.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

    chat_messages = conversation.messages.select_related('sender').all()
    other = conversation.other_participant(request.user)

    return render(request, 'chat/room.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,
        'other': other,
    })


@login_required
@require_POST
def upload_attachment(request, conversation_id):
    """
    Handles picture/video uploads from the composer. Saves the message,
    then broadcasts it over the same WebSocket group the room page is
    listening on, so it appears instantly for both people — including
    the sender, whose composer never touches the WebSocket for uploads.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
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

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{conversation.id}',
        {
            'type': 'chat_message',
            'message': message.text,
            'sender_id': request.user.id,
            'sender_name': request.user.display_name(),
            'timestamp': message.timestamp.strftime('%H:%M'),
            'message_id': message.id,
            'attachment_url': message.attachment.url,
            'attachment_kind': message.attachment_kind(),
        }
    )

    return JsonResponse({'status': 'ok', 'message_id': message.id})
