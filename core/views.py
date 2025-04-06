from django.shortcuts import render

from chats.models import Chat, Message

from django.http import HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth.decorators import login_required

def index(request):
    if request.user.is_authenticated:
        # For authenticated users, get or create their chat
        chat, created = Chat.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, create a session-based chat
        if not request.session.session_key:
            request.session.create()
        
        # Try to find an existing chat with this session ID
        chat = Chat.objects.filter(session_id=request.session.session_key).first()
        
        if not chat:
            # Create a new chat for this anonymous session
            chat = Chat.objects.create(session_id=request.session.session_key)
    
    return HttpResponseRedirect(reverse("core:chat", kwargs={"hash":chat.hash}))

def chat_view(request, hash):
    try:
        chat = Chat.objects.get(hash=hash)
        
        # Verify this user has permission to view this chat
        if chat.user and chat.user != request.user:
            # This is someone else's chat, redirect to their own
            return HttpResponseRedirect(reverse("core:index"))
            
        # For anonymous chats, verify the session matches
        if not request.user.is_authenticated and chat.session_id != request.session.session_key:
            # This anonymous chat belongs to another session
            return HttpResponseRedirect(reverse("core:index"))
            
    except Chat.DoesNotExist:
        return HttpResponseRedirect(reverse("core:index"))
    
    # Only show message history for authenticated users
    if request.user.is_authenticated:
        messages = Message.objects.filter(chat=chat)
    else:
        # For anonymous users, don't show history
        messages = []

    context = {"chat": chat, "messages": messages, "is_authenticated": request.user.is_authenticated}

    return render(request, "core/index.html", context)

def delete_chat(request):
    if request.user.is_authenticated:
        # For authenticated users
        chat = Chat.objects.get(user=request.user)
    else:
        # For anonymous users
        if not request.session.session_key:
            return HttpResponseRedirect(reverse("core:index"))
        chat = Chat.objects.filter(session_id=request.session.session_key).first()
        
    if chat:
        chat.delete()
        
    return HttpResponseRedirect(reverse("core:index"))

def login_view(request):
    return render(request, "core/login.html")

def signup_view(request):
    return render(request, "core/signup.html")