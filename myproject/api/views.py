import os
import tempfile
import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async

from .ml_engine.predictor import predictor   # ← الصحيح

# 1. الدالة دي هتعمل كل الشغل التقيل (حفظ، تحويل، توقع، ومسح الملفات)
def process_video_sync(uploaded_video):
    webm_path = None
    mp4_path = None
    try:
        # Save WebM
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            for chunk in uploaded_video.chunks():
                tmp.write(chunk)
            webm_path = tmp.name

        # Convert to MP4 for OpenCV
        mp4_path = webm_path.replace(".webm", ".mp4")

        subprocess.run([
            "ffmpeg", "-i", webm_path,
            "-vcodec", "libx264",
            "-y", mp4_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Run Predictor
        result = predictor.predict_video(mp4_path)
        return result

    finally:
        # خطوة إضافية ومهمة: مسح الملفات بعد ما نخلص عشان الهارد ميتمليش
        if webm_path and os.path.exists(webm_path):
            os.remove(webm_path)
        if mp4_path and os.path.exists(mp4_path):
            os.remove(mp4_path)

# تحويل الدالة لـ Async عشان تشتغل في مسار (Thread) منفصل
async_process_video = sync_to_async(process_video_sync, thread_sensitive=False)

@csrf_exempt
async def predict_sign(request): # لاحظ إضافة كلمة async هنا
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid method"
        })

    if "video" not in request.FILES:
        return JsonResponse({
            "status": "error",
            "message": "No video uploaded"
        })

    uploaded_video = request.FILES["video"]

    try:
        # 2. استدعاء الدالة التقيلة باستخدام await
        result = await async_process_video(uploaded_video)

        if (not result) or ("error" in result) or not result.get("sentence"):
            return JsonResponse({
                "status": "success",
                "data": {"sentence": "", "words": []}
            })

        return JsonResponse({
            "status": "success",
            "data": {
                "sentence": result["sentence"],
                "words": result.get("words", [])
            }
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })