from django.urls import path
from . import views

app_name = "users_app"

urlpatterns = [
    path("", views.all_users, name="all_users"),
    path("<int:user_id>/", views.user_by_id, name="user_by_id"),
    path("login/", views.login, name="login"),
    path("validate/", views.validate, name="validate"),
]
