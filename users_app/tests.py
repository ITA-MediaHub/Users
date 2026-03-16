from django.test import TestCase
from django.urls import reverse
from json import loads
from argon2 import PasswordHasher
import jwt
from os import environ
from dotenv import load_dotenv

from .models import User

load_dotenv()

def get_valid_token(id, username):
    return jwt.encode({"user_id": id, "username": username}, environ["JWT_SECRET"], algorithm="HS256")
   
def get_invalid_token(id, username):
    return jwt.encode({"user_id": id, "username": username}, "test", algorithm="HS256")

class GetAllUsersTests(TestCase):
    def setUp(self):
        User.objects.all().delete()

    def test_no_users(self):
        """
        If there are no users, an empty array is returned with a 'users' key.
        """
        response = self.client.get(reverse("users_app:all_users"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf-8"), {"users": []})

    def test_some_users(self):
        """
        If there are users in the database, an array of users is returned with a 'users' key.
        """
        User.objects.create(username="John", password="test")
        User.objects.create(username="Jane", password="test")
        response = self.client.get(reverse("users_app:all_users"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf-8"), {"users": [{"user_id": 1, "username": "John"}, {"user_id": 2, "username": "Jane"}]})

class GetUserByIdTests(TestCase):
    def setUp(self):
        User.objects.create(username="John", password="test", id=1)

    def test_get_existing_user(self):
        """
        If a user with the given id exists, data about them is returned.
        """
        response = self.client.get(reverse("users_app:user_by_id", args=(1,)))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf-8"), {"user":{"user_id": 1, "username": "John"}})

    def test_get_non_existing_user(self):
        """
        If a user with the given id does not exist, 404 and an error message are returned.
        """
        response = self.client.get(reverse("users_app:user_by_id", args=(100,)))
        self.assertEqual(response.status_code, 404)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def tearDown(self):
        User.objects.all().delete()

class RegisterUserTests(TestCase):
    def setUp(self):
        User.objects.all().delete()

    def test_register_valid_user(self):
        """
        If valid data for a new user is sent, a new user is created and a success message and user data returned.
        """
        payload = {"username": "John", "password": "test"}
        response = self.client.post(reverse("users_app:all_users"), payload, "application/json")
        self.assertEqual(response.status_code, 201)
        response_json = loads(response.content)
        self.assertTrue("message" in response_json)
        self.assertTrue("user" in response_json)
        self.assertTrue("user_id" in response_json["user"])
        self.assertTrue("username" in response_json["user"])
        user = User.objects.all().first()
        self.assertEqual(user.username, "John")

    def test_non_json_content(self):
        """
        View rejects requests without content type set to "application/json".
        """
        payload = {"username": "John", "password": "test"}
        response = self.client.post(reverse("users_app:all_users"), payload)
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_invalid_json_content(self):
        """
        View rejects requests with invalid JSON content.
        """
        payload = "{\"username: John []]" #idk some nonsense
        response = self.client.post(reverse("users_app:all_users"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_incorrect_fields(self):
        """
        If a request is sent without the "username" and "password" fields, an error is returned.
        """
        payload = {"username": "John"}
        response = self.client.post(reverse("users_app:all_users"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_existing_username(self):
        """
        If a request is sent with an already existing username, an  error is returned.
        """
        User.objects.create(username="John", password="test")
        payload = {"username": "John", "password": "password"}
        response = self.client.post(reverse("users_app:all_users"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_too_long_username(self):
        """
        If a request is sent with a username longer than 20 characters, an error is returned.
        """
        payload = {"username": "JohnathanJohnson1993uwu", "password": "password"}
        response = self.client.post(reverse("users_app:all_users"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_password_stored_securely(self):
        """
        The password is not stored in plain text form following registration.
        """
        payload = {"username": "John", "password": "test"}
        response = self.client.post(reverse("users_app:all_users"), payload, "application/json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.all().first()
        self.assertNotEqual(user.password, "test")

class EditUserTests(TestCase):
    def setUp(self):
        ph = PasswordHasher()
        hashed_password = ph.hash("test")
        User.objects.create(username="John", password=hashed_password, id=1)

    def tearDown(self):
        User.objects.all().delete()

    def test_change_username(self):
        """
        If an authenticated request bearing a valid username different from the user's current username is sent, the new username is applied.
        """
        payload = {"username": "Johnathan"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        response_json = loads(response.content)
        self.assertTrue("message" in response_json)
        self.assertTrue("user" in response_json)
        self.assertEqual(response_json["user"]["user_id"], 1)
        self.assertEqual(response_json["user"]["username"], "Johnathan")
        user = User.objects.all().first()
        self.assertEqual(user.username, "Johnathan")

    def test_change_password(self):
        """
        If an authenticated request bearing a password is sent, the new password is applied.
        """
        payload = {"password": "john123"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        response_json = loads(response.content)
        self.assertTrue("message" in response_json)
        self.assertTrue("user" in response_json)
        self.assertEqual(response_json["user"]["user_id"], 1)
        self.assertEqual(response_json["user"]["username"], "John")
        user = User.objects.all().first()
        ph = PasswordHasher()
        ph.verify(user.password, "john123")

    def test_unauthorized_change(self):
        """
        If a user sends an authenticated request to change another user's details, an error is returned and no change occurs.
        """
        payload = {"username": "Johnathan"}
        token = get_valid_token(2, "Jane")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 403)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        user = User.objects.all().first()
        self.assertEqual(user.username, "John")

    def test_request_with_invalid_authentication(self):
        """
        If a user sends a request with invalid authentication to change someone's details, an error is returned and no change occurs.
        """
        payload = {"username": "Johnathan"}
        token = get_invalid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        user = User.objects.all().first()
        self.assertEqual(user.username, "John")

    def test_unauthenticated_request(self):
        """
        If a user sends a request with no authentication to change someone's details, an error is returned and no change occurs.
        """
        payload = {"username": "Johnathan"}
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json")
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        user = User.objects.all().first()
        self.assertEqual(user.username, "John")

    def test_edit_non_existing_user(self):
        """
        If a user with the given id does not exist, 404 and an error message are returned.
        """
        User.objects.all().delete()

        payload = {"username": "Johnathan"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 404)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_non_json_content(self):
        """
        View rejects requests without content type set to "application/json".
        """
        payload = {"username": "Johnathan"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_invalid_json_content(self):
        """
        View rejects requests with invalid JSON content.
        """
        payload = "{\"username: John []]" #idk some nonsense
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_incorrect_fields(self):
        """
        If a request is sent without the "username" or "password" fields, an error is returned.
        """
        payload = {"hello": "world"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_existing_username(self):
        """
        If a request is sent with an already existing username, an  error is returned.
        """
        User.objects.create(username="Johnathan", password="test")
        
        payload = {"username": "Johnathan"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_too_long_username(self):
        """
        If a request is sent with a username longer than 20 characters, an error is returned.
        """
        payload = {"username": "JohnathanJohnson1993uwu"}
        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), payload, "application/json", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

class DeleteUserTests(TestCase):
    def setUp(self):
        User.objects.create(username="John", password="test", id=1)

    def tearDown(self):
        User.objects.all().delete()

    def test_delete_user(self):
        """
        If an authenticated request is sent from a user to delete themselves, the user is deleted and a success message returned.
        """
        token = get_valid_token(1, "John")
        response = self.client.delete(reverse("users_app:user_by_id", args=(1,)), headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        response_json = loads(response.content)
        self.assertTrue("message" in response_json)
        self.assertEqual(User.objects.all().count(), 0)

    def test_unauthorized_delete(self):
        """
        If a user sends an authenticated request to delete another user, an error is returned and no deletion occurs.
        """
        token = get_valid_token(2, "Jane")
        response = self.client.delete(reverse("users_app:user_by_id", args=(1,)), headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 403)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        self.assertEqual(User.objects.all().count(), 1)

    def test_request_with_invalid_authentication(self):
        """
        If a user sends a request with invalid authentication to delete a user, an error is returned and no deletion occurs.
        """
        token = get_invalid_token(1, "John")
        response = self.client.delete(reverse("users_app:user_by_id", args=(1,)), headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        self.assertEqual(User.objects.all().count(), 1)

    def test_unauthenticated_request(self):
        """
        If a user sends a request with no authentication to delete a user, an error is returned and no deletion occurs.
        """
        response = self.client.delete(reverse("users_app:user_by_id", args=(1,)))
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        self.assertEqual(User.objects.all().count(), 1)
    
    def test_delete_non_existing_user(self):
        """
        If a user with the given id does not exist, 404 and an error message are returned.
        """
        User.objects.all().delete()

        token = get_valid_token(1, "John")
        response = self.client.put(reverse("users_app:user_by_id", args=(1,)), headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 404)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

class LoginTests(TestCase):
    def setUp(self):
        ph = PasswordHasher()
        hashed_password = ph.hash("test")
        User.objects.create(username="John", password=hashed_password, id=1)

    def tearDown(self):
        User.objects.all().delete()

    def test_valid_login(self):
        """
        If a user sends valid login data, they recieve an authentication token with their id and username.
        """
        payload = {"username": "John", "password": "test"}
        response = self.client.post(reverse("users_app:login"), payload, "application/json")
        self.assertEqual(response.status_code, 200)
        response_json = loads(response.content)
        self.assertTrue("message" in response_json)
        self.assertTrue("token" in response_json)

    def test_non_json_content(self):
        """
        View rejects requests without content type set to "application/json".
        """
        payload = {"username": "John", "password": "test"}
        response = self.client.post(reverse("users_app:login"), payload)
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_invalid_json_content(self):
        """
        View rejects requests with invalid JSON content.
        """
        payload = "{\"username: John []]" #idk some nonsense
        response = self.client.post(reverse("users_app:login"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_incorrect_fields(self):
        """
        If a request is sent without both the "username" and "password" fields, an error is returned.
        """
        payload = {"hello": "world"}
        response = self.client.post(reverse("users_app:login"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_non_existing_username(self):
        """
        If a user tries to log in with a non-existing username, an error is sent and they are not logged in.
        """
        payload = {"username": "Jane", "password": "test"}
        response = self.client.post(reverse("users_app:login"), payload, "application/json")
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_incorrect_password(self):
        """
        If a user tries to log in with an incorrect password, an error is sent and they are not logged in.
        """
        payload = {"username": "John", "password": "password"}
        response = self.client.post(reverse("users_app:login"), payload, "application/json")
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

class TokenValidationTests(TestCase):
    def test_valid_token(self):
        """
        If a request is sent with a valid token, the token's claims are returned with a success code.
        """
        payload = {"token": get_valid_token(1, "John")}
        response = self.client.post(reverse("users_app:validate"), payload, "application/json")
        self.assertEqual(response.status_code, 200)
        response_json = loads(response.content)
        self.assertDictEqual(response_json, {"user_id": 1, "username": "John"})

    def test_invalid_token(self):
        """
        If a request is sent with an invalid token, an error message is returned.
        """
        payload = {"token": get_invalid_token(1, "John")}
        response = self.client.post(reverse("users_app:validate"), payload, "application/json")
        self.assertEqual(response.status_code, 401)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_non_json_content(self):
        """
        View rejects requests without content type set to "application/json".
        """
        payload = {"token": get_invalid_token(1, "John")}
        response = self.client.post(reverse("users_app:validate"), payload)
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_invalid_json_content(self):
        """
        View rejects requests with invalid JSON content.
        """
        payload = "{\"username: John []]" #idk some nonsense
        response = self.client.post(reverse("users_app:validate"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)

    def test_no_token_field(self):
        """
        If a request is sent without the "token" field, an error is returned.
        """
        payload = {"hello": "world"}
        response = self.client.post(reverse("users_app:validate"), payload, "application/json")
        self.assertEqual(response.status_code, 400)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
