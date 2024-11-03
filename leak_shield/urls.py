from django.urls import path
from . import views

app_name = 'leak_shield'  # Cambiado de APP_NAME a app_name (lowercase)

urlpatterns = [
    path('messages/', views.slack_messages, name='slack_messages'),
    path('messages/<str:channel_id>/', views.slack_messages,
         name='slack_messages_channel'),
]
