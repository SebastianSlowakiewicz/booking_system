from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings

class Users(AbstractUser):
    IDENTITY_DOCUMENT_TYPES = [
        ("dowod_osobisty", "Dowód osobisty"),
        ("paszport", "Paszport"),
    ]

    phone = PhoneNumberField()
    birth_date = models.DateField(null=True, blank=True)
    identity_document_type = models.CharField(max_length=50, choices=IDENTITY_DOCUMENT_TYPES)
    identity_document_no = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    
class Address(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='address',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    post_code = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    building_no = models.CharField(max_length=50)
    appartment_no = models.CharField(max_length=50, blank=True)