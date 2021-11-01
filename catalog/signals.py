import logging

from django.apps import apps
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.urls import reverse
#from catalog.tasks import send_verification_email

logger = logging.getLogger(__name__)


def user_post_save(sender, instance, signal, *args, **kwargs):
    if not instance.is_verified:
        # Send verification email
        #send_verification_email.delay(instance.pk)
        pass


def init_signals():
    User = apps.get_model(app_label="catalog", model_name="User")

    post_save.connect(user_post_save, sender=User)