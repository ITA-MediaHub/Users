import jwt
from os import environ

def validate_token(token):
    try:
        return jwt.decode(token, environ["JWT_SECRET"], algorithms=["HS256"])
    except jwt.DecodeError:
        return None

def extract_auth_token(request):
    auth_header = request.headers["Authorization"]
    token = auth_header.split(sep=" ")[1] # gets token from "Bearer xyz" formatted header
    return token
