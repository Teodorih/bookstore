from django.db.backends.utils import logger
from django.http import HttpResponse
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from locallibrary.celery import celery_app
from .models import Document
from django.core.files import File
import logging


@celery_app.task
def send_verification_email(user_id):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=user_id)
        logging.warning("Test debug")

        send_mail(
            'Verify your QuickPublisher account',
            'Follow this link to verify your account: '
                'http://localhost:8000%s' % reverse('verify', kwargs={'uuid': str(user.verification_uuid)}),
            'from@quickpublisher.dev',
            [user.email],
            fail_silently=False,
        )
    except UserModel.DoesNotExist:
        logging.warning("Tried to send verification email to non-existing use")


@celery_app.task
def upload_file(file_path, file_name):
    with open(file_path, 'rb') as f:
        file = File(f)
        logger.info("document saved successfully")
        file.name = file_name
        newdoc = Document(docfile=file)
        logger.info("document sav1d 1successfully")
        newdoc.save()
