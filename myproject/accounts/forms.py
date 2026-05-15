from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    SetPasswordForm
)
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# ===============================
# 🟢 Registration
# ===============================
class RegistrationForm(UserCreationForm):
    # 1. بنسمح للمستخدم يكتب مسافة في الواجهة بدون ما يظهرله خطأ
    username = forms.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+\s-]+$',  
                message='Enter a valid username.',
                code='invalid_username'
            )
        ]
    )
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    # 🔥 2. الحل السحري: تحويل المسافة لـ (_) قبل الحفظ في الداتابيز 🔥
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # استبدال المسافات عشان جانجو يقبلها بدون أي إيرور
            username = username.replace(' ', '_')
        return username


# ===============================
# 🟢 Login
# ===============================
class LoginForm(AuthenticationForm):
    pass


# ===============================
# 🔐 Reset Password
# ===============================
class PrettySetPasswordForm(SetPasswordForm):
    pass