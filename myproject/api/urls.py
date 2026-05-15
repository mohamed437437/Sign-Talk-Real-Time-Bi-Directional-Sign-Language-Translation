from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    path("predict-sign/", views.predict_sign, name="predict_sign"),
]
