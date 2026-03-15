from django.http import HttpResponse, JsonResponse
import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from dotenv import load_dotenv
from os import environ
import logging
from .models import User
from .utils import validate_token, extract_auth_token

load_dotenv()

logger = logging.getLogger(__name__)

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
        
        username = request_content.get("username")
        password = request_content.get("password")
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
        token_claims = validate_token(extract_auth_token(request))
        if token_claims is None:
            return JsonResponse({"error": "Invalid authorization token"}, status=401)
        
        if token_claims["user_id"] != user_id:
            return JsonResponse({"error": "Not allowed to modify this user"}, status=403)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User with given ID does not exist."}, status=404)

        if request.content_type != "application/json":
            return JsonResponse({"error": "Expecting JSON content type"}, status=400)
            
        try:
            request_content = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        
        username = request_content.get("username")
        password = request_content.get("password")
        if username is None and password is None:
            return JsonResponse({"error": "Request body must contain at least one of 'username' and 'password' fields"}, status=400)

        if username:
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                return JsonResponse({"error": "User with that username already exists, please choose a different username."}, status=400)
            
            if len(username) > 20:
                return JsonResponse({"error": "Username cannot be longer than 20 characters."}, status=400)
            
            user.username = username
        
        if password:
            ph = PasswordHasher()
            hashed_password = ph.hash(password)
            user.password = hashed_password

        user.save()
        return JsonResponse({"message": "Sucessfully updated user.", "user": {"user_id": user.id, "username": user.username}}, status=200)

    elif request.method == "DELETE":
        token_claims = validate_token(extract_auth_token(request))
        if token_claims is None:
            return JsonResponse({"error": "Invalid authorization token"}, status=401)
        
        if token_claims["user_id"] != user_id:
            return JsonResponse({"error": "Not allowed to delete this user"}, status=403)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User with given ID does not exist."}, status=404)
        
        user.delete()
        return JsonResponse({"message": "Successfully deleted user."}, status=200)

def login(request):
    if request.content_type != "application/json":
        return JsonResponse({"error": "Expecting JSON content type"}, status=400)
        
    try:
        request_content = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    
    username = request_content.get("username")
    password = request_content.get("password")
    if username is None or password is None:
        return JsonResponse({"error": "Request body must contain username and password fields"}, status=400)
    
    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({"error": "Invalid username or password"}, status=401)
    
    ph = PasswordHasher()
    hashed_password = user.password
    try:
        ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return JsonResponse({"error": "Invalid username or password"}, status=401)
    
    token = jwt.encode({"user_id": user.id, "username": user.username}, environ["JWT_SECRET"], algorithm="HS256")
    
    return JsonResponse({"message": "Sucessfully logged in.", "token": token}, status=200)

def validate(request):
    if request.content_type != "application/json":
        return JsonResponse({"error": "Expecting JSON content type"}, status=400)
        
    try:
        request_content = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    
    token = request_content["token"]
    if token is None:
        return JsonResponse({"error": "Request body must contain token field"}, status=400)
    
    decoded_token = validate_token(token)
    if decoded_token is None:
        return JsonResponse({"error": "Provided token is not valid"}, status=401)
    
    return JsonResponse(decoded_token, status=200)
