from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ==========================================
# 1. نموذج البروفايل (Profile Model)
# ==========================================
class Profile(models.Model):
    # ✅ التعديل: غيرنا الاسم إلى chat_profile لمنع التضارب مع accounts
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="chat_profile")
    
    profile_image = models.ImageField(
        upload_to="profile_pics/",
        default="default.png",
        blank=True,
        null=True
    )
    
    is_online = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# --- Signals ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # ✅ التعديل: نتحقق من chat_profile
    if hasattr(instance, 'chat_profile'):
        instance.chat_profile.save()


# ==========================================
# 2. نموذج الرسائل (ChatMessage Model)
# ==========================================
class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ("text", "Text"),
        ("ml_result", "ML Result"),
        ("system", "System"),
        ("image", "Image"), 
    )

    # ✅ التعديل: غيرنا الاسم إلى chat_sent_messages
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sent_messages"
    )

    # ✅ التعديل: غيرنا الاسم إلى chat_received_messages
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_received_messages"
    )

    msg_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default="text"
    )

    message = models.TextField(help_text="Text message, ML result, or Media URL")
    is_seen = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["sender", "receiver"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.message[:30]}"