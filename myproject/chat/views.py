import json
import os
import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q  # 🛑 التعديل: تم إضافة هذا السطر للبحث المتقدم
from .models import ChatMessage, Profile

# استدعاء الـ Agent
from .agent import SmartSignTalkAgent

User = get_user_model()
ai_agent = SmartSignTalkAgent() # تهيئة الـ Agent مرة واحدة

# ==========================================
# 0. عرض قائمة المحادثات (Chat List) - 🔥 الكود الجديد 🔥
# ==========================================
@login_required
def chat_list_view(request):
    # 1. جلب كل الرسائل التي يكون المستخدم الحالي طرفاً فيها (مرسل أو مستقبل) وغير محذوفة
    active_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        is_deleted=False
    ).values_list('sender', 'receiver')

    # 2. استخراج معرفات (IDs) المستخدمين الآخرين من هذه الرسائل
    active_user_ids = set()
    for sender_id, receiver_id in active_messages:
        if sender_id != request.user.id:
            active_user_ids.add(sender_id)
        if receiver_id != request.user.id:
            active_user_ids.add(receiver_id)

    # 3. جلب بيانات هؤلاء المستخدمين فقط لعرضهم في القائمة
    users = User.objects.filter(id__in=active_user_ids)

    # 🛑 تأكد أن مسار الـ HTML هنا مطابق لاسم ملف القائمة عندك
    # إذا كان في مجلد core اكتب "core/chat_list.html" 
    return render(request, "chat/chat_list.html", {
        "users": users
    })

# ==========================================
# 1. عرض الشات وتحميل الصور الشخصية
# ==========================================
@login_required
def chat_view(request, user_id):
    other = get_object_or_404(User, id=user_id)
    
    # 🛑 التعديل هنا: جلب آخر 50 رسالة فقط لحماية المتصفح من التهنيج
    qs = ChatMessage.objects.filter(
        sender__in=[request.user, other],
        receiver__in=[request.user, other],
        is_deleted=False,
    ).order_by("-created_at")[:50] # الترتيب من الأحدث للأقدم وناخد 50
    
    # نعكس القائمة عشان ترجع لترتيب الشات الطبيعي (من الأقدم للأحدث)
    qs = list(qs)[::-1] 

    messages_list = []
    for m in qs:
        sender_pic = ""
        if hasattr(m.sender, 'user_profile') and m.sender.user_profile.profile_image:
            sender_pic = m.sender.user_profile.profile_image.url
        messages_list.append({
            "id": m.id,
            "sender_id": m.sender.id,
            "message": m.message,
            "time": m.created_at.strftime("%H:%M"),
            "sender_pic": sender_pic
        })

    messages_json = json.dumps(messages_list, cls=DjangoJSONEncoder)
    return render(request, "core/chat.html", {
        "other_user": other,
        "other_user_id": other.id,
        "messages_json": messages_json,
    })

# ==========================================
# 2. جلب الهيستوري 
# ==========================================
@login_required
def chat_history(request, other_user_id):
    other = get_object_or_404(User, id=other_user_id)
    
    # 🛑 نفس التعديل هنا
    qs = ChatMessage.objects.filter(
        sender__in=[request.user, other],
        receiver__in=[request.user, other],
        is_deleted=False,
    ).order_by("-created_at")[:50]
    
    qs = list(qs)[::-1]

    messages = []
    for m in qs:
        sender_pic = ""
        if hasattr(m.sender, 'user_profile') and m.sender.user_profile.profile_image:
            sender_pic = m.sender.user_profile.profile_image.url
        messages.append({
            "id": m.id,
            "sender_id": m.sender.id,
            "message": m.message,
            "time": m.created_at.strftime("%H:%M"),
            "sender_pic": sender_pic
        })
    return JsonResponse({"messages": messages})

# ==========================================
# 3. الرفع (تحديث البروفايل أو الميديا)
# ==========================================
@login_required
@require_POST
def upload_media(request, other_user_id):
    other = get_object_or_404(User, id=other_user_id)
    is_profile = request.POST.get("is_profile") == "true"
    f = request.FILES.get("file")

    if not f: return JsonResponse({"error": "No file"}, status=400)

    ext = os.path.splitext(f.name)[1].lower()
    filename = f"chat_uploads/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(filename, f)
    file_url = default_storage.url(saved_path)

    if is_profile:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.profile_image = f 
        profile.save()
        return JsonResponse({"url": profile.profile_image.url, "status": "success"})

    msg = ChatMessage.objects.create(sender=request.user, receiver=other, msg_type="image", message=file_url)
    return JsonResponse({"url": file_url, "time": msg.created_at.strftime("%H:%M"), "id": msg.id})

# ==========================================
# 4. مسح رسالة
# ==========================================
@login_required
@require_POST
def delete_message(request, mid):
    msg = get_object_or_404(ChatMessage, id=mid, sender=request.user, is_deleted=False)
    msg.is_deleted = True
    msg.save(update_fields=["is_deleted"])
    return JsonResponse({"success": True})

# ==========================================
# 5. مسح الشات بالكامل
# ==========================================
@login_required
@require_POST
def clear_chat(request, user_id):
    other = get_object_or_404(User, id=user_id)
    ChatMessage.objects.filter(sender__in=[request.user, other], receiver__in=[request.user, other]).update(is_deleted=True)
    return JsonResponse({"success": True})

# ==========================================
# 6. نقطة الاتصال مع الذكاء الاصطناعي (AI Endpoint)
# ==========================================
@csrf_exempt
@require_POST
def process_agent_message(request):
    try:
        data = json.loads(request.body)
        request_type = data.get("type") 
        
        # 1: Text to Sign
        if request_type == "text_to_sign":
            user_text = data.get("message", "")
            response_data = ai_agent.process_text_to_sign(user_text)
            return JsonResponse(response_data)
            
        # 2: Sign to Text (From SlowFast)
        elif request_type == "sign_to_text":
            detected_words = data.get("words", [])
            confidence = data.get("confidence", 0.0)
            response_data = ai_agent.process_slowfast_output(detected_words, confidence)
            return JsonResponse(response_data)
            
        else:
            return JsonResponse({"status": "error", "message": "Invalid request type. Must be 'text_to_sign' or 'sign_to_text'"}, status=400)
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# ==========================================
# 7. نقطة استقبال الفويس نوت (Voice to Text Endpoint)
# ==========================================
@login_required
@require_POST
def process_voice_note(request):
    if request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        audio_bytes = audio_file.read()
        
        try:
            # 1. حفظ ملف الصوت على السيرفر
            ext = ".webm" 
            filename = f"chat_uploads/voice_{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(filename, audio_file)
            file_url = default_storage.url(saved_path)

            # 2. تفريغ الصوت
            agent_result = ai_agent.transcribe_audio(audio_bytes, audio_file.content_type)
            
            if agent_result.get("status") == "success":
                transcribed_text = agent_result.get("text", "")
                return JsonResponse({
                    "status": "success", 
                    "text": transcribed_text,
                    "audio_url": file_url
                })
            else:
                default_storage.delete(saved_path)
                return JsonResponse(agent_result)

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Agent error: {str(e)}"}, status=500)
            
    return JsonResponse({"status": "error", "message": "No audio file found in request"}, status=400)