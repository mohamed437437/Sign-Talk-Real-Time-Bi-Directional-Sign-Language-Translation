import json
import os
import uuid
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
from chat.models import ChatMessage # تأكد أن اسم التطبيق chat والموديل ChatMessage

User = get_user_model()

# =========================
# Pages
# =========================
def home(request):
    return render(request, "core/home.html")

def about(request):
    return render(request, "core/about.html")

def sign_to_text(request):
    return render(request, "core/sign_to_text.html")

def test_pwa(request):
    return render(request, "core/test_pwa.html")

# =========================
# Details Pages
# =========================
def letter_detail(request, letter):
    from string import ascii_uppercase
    if letter not in ascii_uppercase:
        messages.error(request, "Letter not found.")
        return redirect("core:home")
    return render(request, "core/letter.html", {"letter": letter})

def number_detail(request, num):
    if num not in [str(i) for i in range(1, 11)]:
        messages.error(request, "Number not found.")
        return redirect("core:home")
    return render(request, "core/number.html", {"num": num})

def phrase_detail(request, phrase):
    allowed = {"Hello", "Thank you", "Good morning", "Good night", "How are you?", "I am fine", "My name is", "Nice to meet you"}
    if phrase not in allowed:
        messages.error(request, "Phrase not found.")
        return redirect("core:home")
    return render(request, "core/phrase.html", {"phrase": phrase})

def day_detail(request, day):
    allowed = {"Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    if day not in allowed:
        messages.error(request, "Day not found.")
        return redirect("core:home")
    return render(request, "core/day.html", {"day": day})

# =========================
# Chat Logic
# =========================

@login_required
def chat_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, "core/chat_list.html", {"users": users})

@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        messages.error(request, "لا يمكنك بدء محادثة مع نفسك")
        return redirect("core:home")

    # جلب الرسائل القديمة لعرضها فور فتح الصفحة
    qs = ChatMessage.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user],
        is_deleted=False,
    ).order_by("created_at")

    messages_json = json.dumps(
        [
            {
                "id": m.id,
                "sender_id": m.sender.id,
                "message": m.message,
                "time": m.created_at.strftime("%H:%M"),
            }
            for m in qs
        ],
        cls=DjangoJSONEncoder
    )

    return render(request, "core/chat.html", {
        "other_user": other_user, # لإظهار الاسم والصورة
        "other_user_id": other_user.id,
        "messages_json": messages_json,
    })

# --- الدوال التي كانت تسبب الخطأ (تمت إضافتها) ---

@login_required
@require_POST
def upload_media(request, other_user_id):
    """رفع الصور وتحديث صورة البروفايل عبر AJAX"""
    other = get_object_or_404(User, id=other_user_id)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "No file"}, status=400)

    ext = os.path.splitext(f.name)[1].lower()
    filename = f"chat_uploads/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(filename, f)
    file_url = default_storage.url(saved_path)

    # حفظ الصورة كرسالة ميديا (اختياري)
    msg = ChatMessage.objects.create(
        sender=request.user,
        receiver=other,
        msg_type="image",
        message=file_url,
    )

    return JsonResponse({
        "url": file_url,
        "time": msg.created_at.strftime("%H:%M"),
    })

@login_required
@require_POST
def clear_chat(request, user_id):
    """مسح كل الرسائل بين طرفين"""
    other = get_object_or_404(User, id=user_id)
    ChatMessage.objects.filter(
        sender__in=[request.user, other],
        receiver__in=[request.user, other],
    ).update(is_deleted=True)
    return JsonResponse({"success": True})

@login_required
@require_POST
def delete_message(request, mid):
    """حذف رسالة واحدة فقط"""
    msg = get_object_or_404(ChatMessage, id=mid, sender=request.user)
    msg.is_deleted = True
    msg.save()
    return JsonResponse({"success": True})