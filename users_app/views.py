from django.http import HttpResponse, JsonResponse
import json
from argon2 import PasswordHasher
import jwt
from dotenv import load_dotenv
from os import environ
from .models import User

load_dotenv()

def all_users(request):
    if request.method == "GET":
        users = User.objects.all()
        users_list = [{"user_id": user.id, "username": user.username} for user in users]
        return JsonResponse({"users": users_list})
    
    elif request.method == "POST":
        if request.content_type != "application/json":
            return JsonResponse({"error": "Expecting JSON content type"}, status=400)
        
        try:
            request_content = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        
        username = request_content["username"]
        password = request_content["password"]
        if username is None or password is None:
            return JsonResponse({"error": "Request body must contain username and password fields"}, status=400)
        
        user_exists = User.objects.filter(username=username).exists()
        if user_exists:
            return JsonResponse({"error": "User with that username already exists, please choose a different username."}, status=400)
        
        if len(username) > 20:
            return JsonResponse({"error": "Username cannot be longer than 20 characters."}, status=400)
        
        ph = PasswordHasher()
        hashed_password = ph.hash(password)
        new_user = User(username=username, password=hashed_password)
        new_user.save()
        return JsonResponse({"message": "Sucessfully registered user.", "user": {"user_id": new_user.id, "username": new_user.username}}, status=201)

def user_by_id(request, user_id):
    if request.method == "GET":
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User with given ID does not exist."}, status=404)
        return JsonResponse({"user": {"user_id": user.id, "username": user.username}})
    
    elif request.method == "PUT":
        return HttpResponse(f"editing user {user_id}") #TODO
    elif request.method == "DELETE":
        return HttpResponse(f"Deleting user {user_id}") #TODO

def login(request):
    if request.content_type != "application/json":
        return JsonResponse({"error": "Expecting JSON content type"}, status=400)
        
    try:
        request_content = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    
    username = request_content["username"]
    password = request_content["password"]
    if username is None or password is None:
        return JsonResponse({"error": "Request body must contain username and password fields"}, status=400)
    
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({"error": "Invalid username or password"}, status=401)
    
    ph = PasswordHasher()
    hashed_password = user.password
    if not ph.verify(hashed_password, password):
        return JsonResponse({"error": "Invalid username or password"}, status=401)
    
    token = jwt.encode({"user_id": user.id, "username": user.username}, environ["JWT_SECRET"], algorithm="HS256")
    
    return JsonResponse({"message": "Sucessfully logged in.", "token": token}, status=200)
