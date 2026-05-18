from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import random, string
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'admin')
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLES = [('admin', 'Admin'), ('employee', 'Employee')]

    email         = models.EmailField(unique=True)
    full_name     = models.CharField(max_length=150)
    employee_id   = models.CharField(max_length=20, unique=True)
    phone         = models.CharField(max_length=15, blank=True)
    department    = models.CharField(max_length=100, blank=True)
    role          = models.CharField(max_length=10, choices=ROLES, default='employee')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    date_joined   = models.DateTimeField(auto_now_add=True)
    otp           = models.CharField(max_length=6, blank=True)
    otp_created   = models.DateTimeField(null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name', 'employee_id']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def generate_otp(self):
        self.otp         = ''.join(random.choices(string.digits, k=6))
        self.otp_created = timezone.now()
        self.save(update_fields=['otp', 'otp_created'])
        return self.otp

    def is_otp_valid(self, otp_input):
        if not self.otp or not self.otp_created:
            return False
        expired = timezone.now() > self.otp_created + timezone.timedelta(minutes=5)
        return (not expired) and (self.otp == otp_input)

    def clear_otp(self):
        self.otp = ''
        self.otp_created = None
        self.save(update_fields=['otp', 'otp_created'])
