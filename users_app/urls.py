from django.urls import path
from . import views

app_name = "users_app"

urlpatterns = [
    path("", views.list, name="users list"),
    path("<int:user_id>/", views.get, name="user info"),
    path("<int:user_id>/register", views.register, name="register"),
    path("<int:user_id>/login", views.login, name="login"),
]
