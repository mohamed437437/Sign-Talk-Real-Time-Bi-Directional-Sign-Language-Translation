import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import ChatMessage

User = get_user_model()

# ==========================================
# 🔥 1. Presence Consumer (الخاص بلمبة الأونلاين في قائمة الشات بره)
# ==========================================
class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.global_group = "global_presence"
        await self.channel_layer.group_add(self.global_group, self.channel_name)
        await self.accept()

        await self.update_user_status(True)

        await self.channel_layer.group_send(
            self.global_group,
            {
                "type": "user_status",
                "user_id": self.user.id,
                "status": "online"
            }
        )

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.update_user_status(False)
            
            await self.channel_layer.group_send(
                self.global_group,
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "status": "offline"
                }
            )
            await self.channel_layer.group_discard(self.global_group, self.channel_name)

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_status",
            "user_id": event["user_id"],
            "status": event["status"]
        }))

    @database_sync_to_async
    def update_user_status(self, is_online):
        try:
            if hasattr(self.user, 'chat_profile'):
                self.user.chat_profile.is_online = is_online
                self.user.chat_profile.save()
        except Exception as e:
            print(f"Error updating status: {e}")


# ==========================================
# 2. Chat Consumer (الشات بتاعك الأصلي من غير تغيير باستثناء سطر الإشعار)
# ==========================================
class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.other_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        users = sorted([str(self.user.id), str(self.other_user_id)])
        self.room_group_name = f"chat_{users[0]}_{users[1]}"
        self.user_group_name = f"user_{self.user.id}"
        self.other_user_group_name = f"user_{self.other_user_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()
        await self.update_user_status(True)

        await self.channel_layer.group_send(
            self.other_user_group_name,
            {"type": "user_status", "user_id": self.user.id, "status": "online"}
        )

        # 👇 الكود الجديد: بيبعت إشعار للستة اللي بره عشان اللمبة تنور
        await self.channel_layer.group_send(
            "global_presence",
            {"type": "user_status", "user_id": self.user.id, "status": "online"}
        )

        other_is_online = await self.get_other_user_status()
        await self.send(text_data=json.dumps({
            "type": "user_status",
            "user_id": self.other_user_id,
            "status": "online" if other_is_online else "offline"
        }))

    async def disconnect(self, close_code):
        await self.update_user_status(False)
        await self.channel_layer.group_send(
            self.other_user_group_name,
            {"type": "user_status", "user_id": self.user.id, "status": "offline"}
        )

        # 👇 الكود الجديد: بيبعت إشعار للستة اللي بره عشان اللمبة تطفي
        await self.channel_layer.group_send(
            "global_presence",
            {"type": "user_status", "user_id": self.user.id, "status": "offline"}
        )

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "status_signal":
            if data["status"] == "online":
                await self.update_user_status(True)
            await self.channel_layer.group_send(
                self.other_user_group_name,
                {"type": "user_status", "user_id": self.user.id, "status": data["status"]}
            )
            # إضافة حالة الإشعار العام هنا كمان لو اليوزر بعت سيجنال
            await self.channel_layer.group_send(
                "global_presence",
                {"type": "user_status", "user_id": self.user.id, "status": data["status"]}
            )
            return

        message = data.get("message", "").strip()
        msg_type = data.get("msg_type", "text")

        if not message:
            return

        # ✅ تحديد نوع المرسل من الرسالة نفسها
        if "||CAM||" in message:
            sender_type = "deaf"
        elif message.startswith("[SIGN]"):
            sender_type = "normal"
        else:
            sender_type = "normal"

        msg = await self.save_message(message, msg_type)
        sender_pic = await self.get_user_profile_pic(self.user)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": msg.id,
                "message": msg.message,
                "msg_type": msg.msg_type,
                "sender_id": msg.sender.id,
                "sender": msg.sender.username,
                "sender_pic": sender_pic,
                "sender_type": sender_type,
                "time": msg.created_at.strftime("%H:%M"),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "message": event["message"],
            "msg_type": event["msg_type"],
            "sender": event["sender"],
            "sender_id": event["sender_id"],
            "sender_pic": event.get("sender_pic", ""),
            "sender_type": event.get("sender_type", "normal"),
            "time": event["time"],
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_status",
            "user_id": event["user_id"],
            "status": event["status"]
        }))

    @database_sync_to_async
    def get_other_user_status(self):
        try:
            other = User.objects.get(id=self.other_user_id)
            if hasattr(other, 'chat_profile'):
                return other.chat_profile.is_online
            return False
        except:
            return False

    @database_sync_to_async
    def save_message(self, message, msg_type):
        OtherUser = User.objects.get(id=self.other_user_id)
        return ChatMessage.objects.create(
            sender=self.user,
            receiver=OtherUser,
            message=message,
            msg_type=msg_type
        )

    @database_sync_to_async
    def get_user_profile_pic(self, user):
        try:
            if hasattr(user, 'chat_profile') and user.chat_profile.profile_image:
                return user.chat_profile.profile_image.url
            return ""
        except:
            return ""

    @database_sync_to_async
    def update_user_status(self, is_online):
        try:
            if hasattr(self.user, 'chat_profile'):
                self.user.chat_profile.is_online = is_online
                self.user.chat_profile.save()
        except Exception as e:
            print(f"Error updating status: {e}")