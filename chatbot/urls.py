from django.urls import path
from .views import chat_api, widget, chat_message

app_name = 'chatbot'

urlpatterns = [
    path('api/', chat_api, name='api'),
    path('widget/', widget, name='widget'),
    path('chat/', chat_message, name='chat_message'),
]
