from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    
    email = models.EmailField(unique=True, blank=False)
    display_name = models.CharField(max_length=10, blank=True)
    