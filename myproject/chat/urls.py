from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # 👇 المسار الجديد الخاص بقائمة المحادثات (Chat List)
    path("", views.chat_list_view, name="chat_list"),

    # مسارات الشات القديمة بتاعتك
    path("<int:user_id>/", views.chat_view, name="chat"),
    path("<int:other_user_id>/messages/", views.chat_history, name="chat_history"),
    path("upload/media/<int:other_user_id>/", views.upload_media, name="upload_media"),
    path("message/<int:mid>/delete/", views.delete_message, name="delete_message"),
    path("<int:user_id>/clear/", views.clear_chat, name="clear_chat"),
    
    # المسارات الخاصة بالذكاء الاصطناعي (الـ Agent)
    path("agent/process/", views.process_agent_message, name="process_agent"),
    path('api/process-voice/', views.process_voice_note, name='process_voice'),
]