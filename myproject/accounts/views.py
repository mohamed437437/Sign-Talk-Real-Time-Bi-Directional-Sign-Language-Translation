from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
import random

# استيراد الفورم الخاصة بك
from .forms import (
    RegistrationForm,
    LoginForm,
    PrettySetPasswordForm,
)

# ===============================
# 🟢 Register (تم الإصلاح ✅)
# ===============================
def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # 🔥 الحل السحري لمشكلة تعدد الـ Backends 🔥
            # بنقول لجانغو يستخدم الـ ModelBackend العادي للدخول دلوقتي
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            login(request, user)
            messages.success(request, "Account created successfully")
            return redirect("core:home")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


# ===============================
# 🟢 Login
# ===============================
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully")
            return redirect("core:home")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


# ===============================
# 🟢 Logout
# ===============================
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out")
    return redirect("core:home")


# =================================================
# 🔐 Password Reset via OTP
# =================================================
def reset_password_otp_request(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not found")
            return render(request, "accounts/reset_password_otp_request.html")

        otp = str(random.randint(100000, 999999))
        
        # 🔥 طباعة الكود في التيرمينال لتسهيل الاختبار 🔥
        print(f"\n\n{'='*40}\n👉 YOUR OTP IS: {otp} 👈\n{'='*40}\n\n")

        request.session["reset_email"] = email
        request.session["reset_otp"] = otp
        request.session["otp_expiry"] = (
            timezone.now() + timezone.timedelta(minutes=10)
        ).timestamp()
        request.session["otp_attempts"] = 0

        # محاولة إرسال الإيميل
        try:
            send_mail(
                "Password Reset OTP",
                f"Your OTP is: {otp}",
                None,
                [email],
                fail_silently=False, 
            )
            messages.info(request, "OTP sent to your email")
        except Exception as e:
            # إذا فشل الإرسال، اطبع الخطأ لكن اسمح للمستخدم بالمرور لأن الكود ظهر في التيرمينال
            print(f"Error sending email: {e}")
            messages.warning(request, "Could not send email, check server console for OTP.")

        return redirect("accounts:reset_otp_verify")

    return render(request, "accounts/reset_password_otp_request.html")


def reset_password_otp_verify(request):
    if not request.session.get("reset_email"):
        return redirect("accounts:reset_otp_request")

    if timezone.now().timestamp() > request.session.get("otp_expiry", 0):
        request.session.flush()
        messages.error(request, "OTP expired")
        return redirect("accounts:reset_otp_request")

    if request.method == "POST":
        entered = request.POST.get("otp")
        if entered == request.session.get("reset_otp"):
            return redirect("accounts:reset_password_set")

        messages.error(request, "Invalid OTP")

    return render(request, "accounts/reset_password_otp_verify.html")


def reset_password_set(request):
    email = request.session.get("reset_email")
    if not email:
        return redirect("accounts:reset_otp_request")

    user = User.objects.get(email=email)

    if request.method == "POST":
        form = PrettySetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            request.session.flush()
            messages.success(request, "Password reset successfully")
            return redirect("accounts:login")
    else:
        form = PrettySetPasswordForm(user=user)

    return render(request, "accounts/reset_password_set.html", {"form": form})


# ===============================
# 🟢 Resend OTP (إعادة إرسال الرمز)
# ===============================
def resend_otp(request):
    # 1. إحضار الإيميل من الجلسة الحالية
    email = request.session.get("reset_email")
    
    # إذا لم يكن الإيميل موجوداً (انتهت الجلسة)، نعيده للبداية
    if not email:
        messages.error(request, "انتهت الجلسة، حاول مرة أخرى.")
        return redirect("accounts:reset_otp_request")

    # 2. إنشاء كود OTP جديد
    new_otp = str(random.randint(100000, 999999))
    
    # 🔥 طباعة الكود الجديد في التيرمينال 🔥
    print(f"\n\n{'='*40}\n👉 RESENT OTP IS: {new_otp} 👈\n{'='*40}\n\n")
    
    # 3. تحديث البيانات في الجلسة (Session)
    request.session["reset_otp"] = new_otp
    request.session["otp_expiry"] = (
        timezone.now() + timezone.timedelta(minutes=10)
    ).timestamp()
    
    # 4. إرسال الإيميل الجديد
    try:
        send_mail(
            "Resent Password Reset OTP",
            f"Your new OTP is: {new_otp}",
            None,
            [email],
            fail_silently=False,
        )
        messages.success(request, "تم إرسال رمز جديد إلى بريدك الإلكتروني.")
    except Exception as e:
        print(f"Error sending email: {e}")
        messages.warning(request, "فشل إرسال الإيميل، راجع التيرمينال لمعرفة الكود.")

    return redirect("accounts:reset_otp_verify")