from django.db import models

class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=97) # based on testing argon2 password hasher output, idk man

    def __str__(self):
        return self.username

