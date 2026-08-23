from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .ai_reply import generate_decline_reply
from .models import Conversation, Message

User = get_user_model()


@login_required
def inbox(request):
    conversations = (
        Conversation.objects
        .filter(Q(student=request.user) | Q(professor=request.user))
        .select_related('student', 'professor')
        .prefetch_related('messages')
        .order_by('-created_at')
    )
    conversations = [
        {
            'conversation': conversation,
            'other': conversation.other_participant(request.user),
            'last_message': conversation.messages.last(),
        }
        for conversation in conversations
    ]
    return render(request, 'directMessage/inbox.html', {'conversations': conversations})


@login_required
def professor_list(request):
    professors = User.objects.filter(is_professor=True).order_by('username')
    return render(request, 'directMessage/professor_list.html', {'professors': professors})


@login_required
@require_POST
def conversation_start(request, professor_id):
    professor = get_object_or_404(User, pk=professor_id, is_professor=True)
    conversation, _ = Conversation.objects.get_or_create(student=request.user, professor=professor)
    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(Q(student=request.user) | Q(professor=request.user)),
        pk=conversation_id,
    )
    return render(request, 'directMessage/conversation_detail.html', {
        'conversation': conversation,
        'other': conversation.other_participant(request.user),
        'messages_list': conversation.messages.select_related('sender'),
    })


@login_required
@require_POST
def message_create(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(Q(student=request.user) | Q(professor=request.user)),
        pk=conversation_id,
    )
    body = request.POST.get('body', '').strip()
    if body:
        Message.objects.create(conversation=conversation, sender=request.user, body=body)
    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
@require_POST
def ai_decline_reply(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id, professor=request.user)
    Message.objects.create(conversation=conversation, sender=request.user, body=generate_decline_reply())
    return redirect('conversation_detail', conversation_id=conversation.id)
