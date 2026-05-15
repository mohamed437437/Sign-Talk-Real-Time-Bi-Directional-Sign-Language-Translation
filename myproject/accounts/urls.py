from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("reset-password/", views.reset_password_otp_request, name="reset_otp_request"),
    path("reset-password/verify/", views.reset_password_otp_verify, name="reset_otp_verify"),
    
    # --- أضف هذا السطر ---
    path("reset-password/resend/", views.resend_otp, name="resend_otp"),
    # ---------------------

    path("reset-password/set/", views.reset_password_set, name="reset_password_set"),
]