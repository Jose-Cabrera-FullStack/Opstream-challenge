from django.urls import path
from leak_shield import views

app_name = 'leak_shield'

urlpatterns = [
    path('messages/', views.slack_messages, name='slack_messages'),
    path('messages/<str:channel_id>/', views.slack_messages,
         name='slack_messages_channel'),
]
