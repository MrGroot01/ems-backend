"""
ai_assistant/urls.py
URL configuration for the AI assistant app.

ADD TO YOUR MAIN urls.py:
    from django.urls import path, include
    urlpatterns = [
        ...
        path('api/ai-assistant/', include('ai_assistant.urls')),
    ]
"""

from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.ai_assistant_chat, name="ai-assistant-chat"),
]