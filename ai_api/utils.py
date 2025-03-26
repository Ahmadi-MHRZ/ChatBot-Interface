from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from cerebras.cloud.sdk import Cerebras
import httpx
from chats.models import Message, Chat

# Persistent client configuration
http_client = httpx.Client(verify=True)
client = Cerebras(
    api_key=settings.CEREBRAS_API_KEY,
    http_client=http_client
)

chat_sessions = dict()

def initialize_ai_chat(chat_hash):
    if chat_hash not in chat_sessions:
        chat_sessions[chat_hash] = {
            "messages": [
                {
                    "role": "system",
                    "content": ""  # Optional system prompt
                }
            ]
        }

def send_message_to_ai(chat_hash, message):
    chat_data = chat_sessions.get(chat_hash)
    chat_model = Chat.objects.get(hash=chat_hash)
    
    if not chat_data:
        return HttpResponseRedirect(reverse("core:index"))

    # Add user message to history
    chat_data["messages"].append({"role": "user", "content": message})
    Message.objects.create(chat=chat_model, text=message, from_ai=False)

    try:
        # Get AI response (non-streaming version)
        completion = client.chat.completions.create(
            messages=chat_data["messages"],
            model="llama3.1-8b",
            max_completion_tokens=500,
            stream=False,  # Single response instead of streaming
            temperature=0.7
        )
        
        ai_response = completion.choices[0].message.content
        
        # Add AI response to history and save
        chat_data["messages"].append({"role": "assistant", "content": ai_response})
        Message.objects.create(chat=chat_model, text=ai_response, from_ai=True)
        
        return ai_response
        
    except Exception as e:
        error_response = f"Sorry, I'm having trouble responding. ({str(e)})"
        Message.objects.create(chat=chat_model, text=error_response, from_ai=True)
        return error_response