import uuid
import json
import re
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from .models import ChatSession, ChatMessage
from .rules import detect_intent, handle_message
from .handlers import handle_intent, handle_payment_lookup, handle_generic_status
from .services import (
    lookup_payment_by_phone,
    lookup_payment_by_reference,
    format_payment_response,
)

PHONE_RE = re.compile(r"(07\d{8}|2547\d{8})")

# Enforce chatbot auth mode via settings
CHATBOT_ALLOW_ANONYMOUS = getattr(settings, "CHATBOT_ALLOW_ANONYMOUS", True)


@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # allow legacy form POSTs (widget) and JSON POSTs (api)
    text = request.POST.get('message', '') or ''

    # accept an optional client-provided session_id (persisted in localStorage)
    client_session = request.POST.get('session_id') or None

    if not text:
        # try JSON body
        try:
            payload = json.loads(request.body.decode())
            text = payload.get('message', '')
            if not client_session:
                client_session = payload.get('session_id')
        except Exception:
            text = ''

    # auth mode enforcement
    if not CHATBOT_ALLOW_ANONYMOUS and (not getattr(request, 'user', None) or request.user.is_anonymous):
        return JsonResponse({'error': 'authentication_required'}, status=401)

    # If client provided a session id, prefer and persist it in server session
    session_id = client_session or request.session.get('chat_id')
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

    return JsonResponse({'reply': reply, 'session_id': session_id})


def widget(request):
    # simple widget template
    return render(request, 'chatbot/widget.html')


@csrf_exempt
@require_POST
def chat_message(request):
    # AUTH enforcement
    if not CHATBOT_ALLOW_ANONYMOUS and (not getattr(request, 'user', None) or request.user.is_anonymous):
        return JsonResponse({'error': 'authentication_required'}, status=401)

    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    message = (payload.get('message') or '').strip()
    if not message:
        return JsonResponse({'reply': 'Please send a message.'})

    intent_data = detect_intent(message)
    intent = intent_data.get('intent')

    # fallback to AI only when rules return unknown
    if not intent or intent == 'unknown':
        from .ai import ai_detect_intent
        intent_data = ai_detect_intent(message)
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
