from django.urls import re_path
from .consumers import ChatConsumer, PresenceConsumer

websocket_urlpatterns = [
    # 👇 المسار الجديد الخاص بلمبة الأونلاين (قائمة المستخدمين)
    re_path(r"ws/presence/$", PresenceConsumer.as_asgi()),
    
    # المسار القديم الخاص بالشات (زي ما هو)
    re_path(r"ws/chat/(?P<user_id>\d+)/$", ChatConsumer.as_asgi()),
]