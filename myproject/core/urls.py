from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),

    # === مسارات المحادثة (Chat) ===
    # قائمة الأشخاص المتاحين للدردشة
    path("chat/", views.chat_list, name="chat_list"),
    
    # صفحة المحادثة مع مستخدم معين
    path("chat/<int:user_id>/", views.chat_view, name="chat_view"),
    
    # رفع الصور أو الفيديو أو البروفايل (عبر Ajax)
    path("upload_media/<int:other_user_id>/", views.upload_media, name="upload_media"),
    
    # مسح المحادثة بالكامل بين طرفين
    path("clear_chat/<int:user_id>/", views.clear_chat, name="clear_chat"),
    
    # حذف رسالة واحدة فقط
    path("delete_message/<int:mid>/", views.delete_message, name="delete_message"),

    # === مسارات المشروع الأخرى ===
    path("sign-to-text/", views.sign_to_text, name="sign_to_text"),
    path("test-pwa/", views.test_pwa, name="test_pwa"),

    path("letter/<str:letter>/", views.letter_detail, name="letter_detail"),
    path("number/<str:num>/", views.number_detail, name="number_detail"),
    path("phrase/<path:phrase>/", views.phrase_detail, name="phrase_detail"),
    path("day/<str:day>/", views.day_detail, name="day_detail"),
]