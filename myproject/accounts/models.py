from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. نموذج البروفايل (تخزين بيانات المستخدم الشخصية)
class Profile(models.Model):
    # استخدام user_profile يسهل الوصول للبيانات: request.user.user_profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    profile_image = models.ImageField(
        upload_to="profile_pics/",
        default="default.png",
        blank=True,
        null=True
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# نظام الـ Signals لضمان إنشاء بروفايل فوراً لأي مستخدم جديد (مهم جداً)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # التأكد من وجود البروفايل قبل محاولة الحفظ
    if hasattr(instance, 'user_profile'):
        instance.user_profile.save()


# 2. نموذج رسائل الشات (ChatMessage)
class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ("text", "Text"),
        ("ml_result", "ML Result"),
        ("system", "System"),
        ("image", "Image"), 
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    msg_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default="text"
    )

    message = models.TextField(
        help_text="Text message, ML result, or Media URL"
    )

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