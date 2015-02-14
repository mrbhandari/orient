from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    active_user = models.BooleanField(default=True)
    merchant = models.CharField(max_length = 1000, default='unknown')


#Gets or creates if users properties don't exist
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

