import uuid
import json
import re
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render
from .models import ChatSession, ChatMessage
from .rules import detect_intent, handle_message
from .handlers import handle_intent, handle_payment_lookup, handle_generic_status
from .services import (
    lookup_payment_by_phone,
    lookup_payment_by_reference,
    format_payment_response,
)

PHONE_RE = re.compile(r"(07\d{8}|2547\d{8})")


@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    text = request.POST.get('message', '')
    session_id = request.session.get('chat_id')
    if not session_id:
        session_id = uuid.uuid4().hex
        request.session['chat_id'] = session_id

    session, _ = ChatSession.objects.get_or_create(
        session_id=session_id,
        defaults={'user': request.user if request.user.is_authenticated else None}
    )

    ChatMessage.objects.create(
        session=session,
        sender='user',
        message=text
    )

    reply = handle_message(text) or "I didn't understand that. Can you rephrase or try another question?"

    ChatMessage.objects.create(
        session=session,
        sender='bot',
        message=reply
    )

    return JsonResponse({'reply': reply})


def widget(request):
    # simple widget template
    return render(request, 'chatbot/widget.html')


@csrf_exempt
@require_POST
def chat_message(request):
    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    message = (payload.get('message') or '').strip()
    if not message:
        return JsonResponse({'reply': 'Please send a message.'})

    intent_data = detect_intent(message)
    intent = intent_data.get('intent')

    if intent == 'payment_lookup':
        response = handle_payment_lookup(intent_data.get('entities', {}))
    elif intent == 'payment_status_generic' or intent == 'payment_lookup_prompt':
        response = handle_generic_status()
    else:
        # fallback to unknown
        response = {
            'reply': '🤖 I didn’t understand that. You can ask me about a payment status.',
            'status': 'unknown',
        }

    return JsonResponse({
        'reply': response.get('reply'),
        'intent': intent,
        'confidence': intent_data.get('confidence'),
    })
