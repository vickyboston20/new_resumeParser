from django.db import models
# from django.contrib.auth.models import User
# for deleting media files after record is deleted
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


# Create your models here.
class User(AbstractUser):
    username = models.CharField(blank=True, null=True, max_length=50)
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return "{}".format(self.email)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    empId = models.CharField(max_length=10)
    dob = models.DateField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True)


class UserDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=255, null=True, blank=True)
    email = models.CharField('Email', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(
        'Mobile Number', max_length=255, null=True, blank=True)
    education = models.CharField(
        'Education', max_length=255, null=True, blank=True)
    educations = models.CharField(
        'Educations', max_length=255, null=True, blank=True)
    skills = models.CharField('Skills', max_length=1000, null=True, blank=True)
    experience = models.CharField(
        'Experience', max_length=1000, null=True, blank=True)
    experiences = models.CharField(
        'Experiences', max_length=1000, null=True, blank=True)
    uploaded_on = models.DateTimeField('Uploaded On', auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name()


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.FileField('Upload Resumes', upload_to='resumes/')
    last_uploaded_on = models.DateTimeField('Uploaded On', auto_now_add=True)

    def __str__(self):
        return self.user.email


# delete the resume files associated with each object or record
@receiver(post_delete, sender=Resume)
def submission_delete(sender, instance, **kwargs):
    instance.resume.delete(False)

