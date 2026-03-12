from django.http import HttpResponse

def list(request): # rename to list or get all or sth after tutorial :)
    return HttpResponse("Hello from index")

def get(request, user_id):
    return HttpResponse(f"attempting to read data from user {user_id}")

def register(request):
    return HttpResponse("creating user")

def login(request):
    return HttpResponse("attempting to log in")

def update(request, user_id):
    return HttpResponse(f"attempting to update user {user_id}")

def delete(request, user_id):
    return HttpResponse(f"attempting to delete user {user_id}")
