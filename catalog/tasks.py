from django.db.backends.utils import logger
from django.http import HttpResponse
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from locallibrary.celery import celery_app
from .models import Document
from django.core.files import File
import logging

import os
from zipfile import ZipFile
from celery import shared_task
from PIL import Image
from django.conf import settings


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



@shared_task
def make_thumbnails(file_path, thumbnails=[]):
    os.chdir(settings.IMAGES_DIR)
    path, file = os.path.split(file_path)
    file_name, ext = os.path.splitext(file)
    zip_file = f"{file_name}.zip"
    results = {'archive_path': f"{settings.MEDIA_URL}images/{zip_file}"}
    try:
        img = Image.open(file_path)
        zipper = ZipFile(zip_file, 'w')
        zipper.write(file)
        os.remove(file_path)
        for w, h in thumbnails:
            img_copy = img.copy()
            img_copy.thumbnail((w, h))
            thumbnail_file = f'{file_name}_{w}x{h}.{ext}'
            img_copy.save(thumbnail_file)
            zipper.write(thumbnail_file)
            os.remove(thumbnail_file)
        img.close()
        zipper.close()
    except IOError as e:
        print(e)
    return results